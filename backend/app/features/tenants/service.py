from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from app.shared.errors import BaseAppException, ConflictError, BadRequestError, NotFoundError
from app.infrastructure.observability import log
from app.features.users.repository import UserRepository
from app.infrastructure.clients import get_supabase_admin

from .models import Tenant, TenantMembers
from .repository import TenantMembersRepository, TenantRepository
from .schemas import TenantCreate, TenantUpdate, TenantResponse, StaffAccountCreate, StaffAccountUpdate, StaffAccountResponse

class TenantService:
    """
    Tenant management service handling CRUD operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TenantRepository(session)

    # === Read Operations ===

    # Admin Operations
    async def get_all_tenants(self) -> List[TenantResponse]:
        """"""
        log.info("tenant.get.all", admin="admin.routes")
        return await self.repo.get_all()

    async def get_tenant(self, identifier: uuid.UUID | str) -> TenantResponse:
        """"""
        log.info("tenant.get", admin="admin.routes")

        tenant = await self.repo.get_by_identifier(identifier)

        if not tenant:
            raise NotFoundError("Tenant not found")
        
        return tenant

    # === Write Operation ===

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        """Create"""
        log.info("tenant.creating", admin="admin.routes")

        try:

            slug = await self.repo.generate_unique_slug(data.name)

            tenant = await self.repo.create(slug=slug, **data.model_dump())

            log.info(
                "tenant.create",
                name=tenant.name
            )

            return tenant

        except IntegrityConstraintError as e:
            log.warning(
                "tenant.create.integrity_error",
                name=data.name,
                error=str(e)
            )
            raise ConflictError("Create violates constraints")
        except DatabaseError as e:
            log.error(
                "tenant.database.error",
                error=str(e),
            )
            raise BaseAppException("Failed to save tenant")
    
    # Would do update, and disable (No delete, We ain't deleting tenants ma boi)
    async def update_tenant(self, identifier: uuid.UUID | str, data: TenantUpdate) -> Tenant:
        """ """
        log.info("tenant.updating", admin="admin.routes")

        tenant = await self.get_tenant(identifier)

        try:
            updated_data = data.model_dump(exclude_unset=True)
            log.info(
                "tenant.update",
                identifier=identifier,
                updated_field = list(updated_data.keys())
            )
            return await self.repo.update(tenant, **updated_data)

        except IntegrityConstraintError as e:
            log.warning(
                "tenant.update.integrity_error",
                name=data.name,
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "tenant.database.error",
                error=str(e),
            )
            raise BaseAppException("Failed to update tenant")
        
        
class TenantMemberService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TenantMembersRepository(session)
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)
        self.supabase = get_supabase_admin()
    
    async def get_all_tenant_members(self, tenant_id: uuid.UUID) -> List[StaffAccountResponse]:
        """"""
        log.info("tenant.member.get.all", tenant_id=tenant_id)
        members = await self.repo.get_many(tenant_id=tenant_id)
        return [self._to_staff_response(m) for m in members]

    async def get_tenant_member(self, tenant_id: uuid.UUID, identifier: str | uuid.UUID) -> TenantMembers:
        """"""
        member = await self.repo.get_one(tenant_id=tenant_id, identifier=identifier) 
        
        if not member:
            raise NotFoundError("Member not found")

        log.info(
            "tenant.member.get",
            tenant_id=tenant_id,
            tenant_member_id=identifier
        )
        
        return self._to_staff_response(member)
    
    # Tenant based account creation (These accounts are solely for this system)
    async def create_account(self, tenant_id: uuid.UUID, data: StaffAccountCreate):
        try:
            email, slug = await self._make_email(tenant_id, data.username)

            auth_response = self.supabase.auth.admin.create_user({
                'email': email,
                'password': data.password,
                'email_confirm': True,
                # "user_metadata": {
                #     'username': data.username
                # }
            })

        except Exception as e:
            if "already registered" in str(e).lower():
                raise ConflictError("Username already taken")
            raise BadRequestError(f"Failed to create account {str(e)}")

        try: 
            user = await self.user_repo.create(
                supabase_user_id=auth_response.user.id,
                email=email,
                username=data.username,
                is_active=True,
                is_email_verified=True
            )      

            member = await self.repo.create(
                user_id=user.id,
                tenant_id=tenant_id,
                is_active=True
            )

            log.info(
                "tenant.member.create",
                username=data.username,
                tenant=slug,
            )

            return StaffAccountResponse(
                id=user.id,
                username=user.username,
                role=member.role,
                is_active=member.is_active
            )

        except Exception as e:
            log.critical("tenant.account.sync_failed", supabase_id=auth_response.user.id, error=str(e))
            raise BaseAppException("Account created but failed to sync local permissions.")
        
    async def update_account(self, tenant_id: uuid.UUID, tenant_member_id: uuid.UUID, data: StaffAccountUpdate):
        """"""

        member = await self.get_tenant_member(tenant_id, tenant_member_id)
        try:
            updated_data = data.model_dump(exclude_unset=True)
            log.info(
                "tenant.members.update",
                tenant_member_id=member.id,
                updated_field=list(updated_data.keys())
            )
            return await self.repo.update(member, **updated_data)
        except IntegrityConstraintError as e:
            log.warning(
                "tenant.update.integrity_error",
                tenant_id=tenant_id,
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "tenant.database.error",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise BaseAppException("Failed to update tenant member")

    # Only if owner finds member to cluttered or daghan na kaayo haha
    async def delete_account(self, tenant_id: uuid.UUID, tenant_member_id: uuid.UUID) -> None:
        """"""
        member = await self.get_tenant_member(tenant_id, tenant_member_id)
        
        try:
            log.info(
                "tenant.member.deleted",
                tenant_id=tenant_id,
                tenant_member_id=tenant_member_id
            )
            await self.repo.delete(member)
        except DatabaseError as e:
            log.error(
                "tenant.database.error",
                tenant_id=tenant_id,
                error=str(e)
            )
            raise BaseAppException(f"{e}")

    # return email and slug (I need slug in creation of member accounts :>)
    async def _make_email(self, tenant_id: uuid.UUID, username: str) -> tuple[str, str]:
        """Make an email credentials"""

        tenant = await self.tenant_repo.get_by_id(tenant_id)

        if not tenant:
            raise NotFoundError("Tenant not found")

        email = f"{username}@{tenant.slug}.keta.com"

        return email, tenant.slug
    
    def _to_staff_response(self, member: TenantMembers) -> StaffAccountResponse:
        return StaffAccountResponse(
            id=member.id,
            username=member.user.username,
            role=member.role,
            is_active=member.is_active,
        )




   