from supabase import Client, AuthApiError
from sqlalchemy.ext.asyncio import AsyncSession


from app.infrastructure.clients import get_supabase_admin
from app.features.users.repository import UserRepository
from app.features.users.models import User
from .schemas import SignInRequest, SignUpRequest
from app.infrastructure.observability import log
from app.shared.errors.exceptions import BadGatewayError, BadRequestError, UnauthorizedError


class AuthService:
    """
    Authentication service handling Supabase auth operations
    and syncing with local database.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)
        self.supabase: Client = get_supabase_admin()

    async def sign_up(self, data: SignUpRequest) -> dict:
        """
        Register a new user with Supabase and sync to local database.

        Args:
            data: SignUpRequest containing email, password, and username.

        Returns:
            A dict containing user_id, email, and requires_email_confirmation flag.
            If email confirmation is enabled, session will be None until verified.

        Raises:
            BadRequestError: If user already exists or sign up fails.
            BadGatewayError: If Supabase connection fails.
        """
        try:

            # Sign up with Supabase
            auth_response = self.supabase.auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {
                    "data": {
                        "username": data.username
                    }
                }
            })

            if not auth_response.user:
                raise BadRequestError("Failed to create user")

            # Sync user to local database
            await self.repo.sync_from_supabase(
                supabase_user_id=auth_response.user.id,
                email=data.email,
                username=data.username,
                is_email_verified=False
            )

            log.info(
                "auth.user.signed.up",
                email=data.email
            )

            requires_confirmation = auth_response.session is None
            
            return {
                "user_id": auth_response.user.id,
                "email": auth_response.user.email,
                "requires_email_confirmation": requires_confirmation
            }

        except AuthApiError as e:
            if "already registered" in str(e).lower():
                raise BadRequestError("User already registered. Please sign in or request a new verification email.")
            raise BadRequestError(f"Sign up failed: {str(e)}")
        except BadRequestError:
            raise  
        except BadGatewayError as e:
            log.error(
                "auth.supabase.error",
            )
            raise BadGatewayError(f"Failed to connect to Supabase: {str(e)}")

    
    async def sign_in(self, data: SignInRequest) -> dict:
        """
        Authenticate a user with Supabase credentials.

        Args:
            data: SignInRequest containing email and password.

        Returns:
            A dict containing access_token, refresh_token, expires_in, and user info.

        Raises:
            UnauthorizedError: If credentials are invalid or email not verified.
        """

        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })

            if not auth_response.session:
                if auth_response.user:
                    raise UnauthorizedError(
                        "Please verify your email before signing in. Check your inbox for the confirmation link."
                    )
                raise UnauthorizedError("Invalid credentials")
                
            if auth_response.user:
                await self.repo.sync_from_supabase(
                    supabase_user_id=auth_response.user.id,
                    email=auth_response.user.email,
                    is_email_verified=auth_response.user.email_confirmed_at is not None
                )

            user = await self.repo.get_by_supabase_id(auth_response.user.id)
            
            log.info(
                "auth.user.signed.in",
                email=data.email
            )

            return {
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "expires_in": auth_response.session.expires_in,
                "user": {
                    "id": user.id,
                    "email": auth_response.user.email
                }
            }
        except UnauthorizedError:
            raise
        except Exception as e:
            log.error("auth.signin.error", error=str(e))
            raise UnauthorizedError("Invalid credentials")

    def resend_verification_email(self, email: str) -> dict:
        """
        Resend verification email for unverified users.

        Args:
            email: The email address to send verification to.

        Returns:
            A dict containing a success message.

        Raises:
            BadRequestError: If email cannot be sent (user not found, already verified, etc.).
        """
        try:
            self.supabase.auth.resend({
                "type": "signup",
                "email": email
                })
            log.info("auth.verification.resent", email=email)
            return {"message": "Verification email sent. Please check your inbox."}
        except AuthApiError as e:
            log.error("auth.resend.error", email=email, error=str(e))
            raise BadRequestError(f"Could not resend verification email: {str(e)}")