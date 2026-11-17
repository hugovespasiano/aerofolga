export type OrgRole = "owner" | "admin" | "member";

export type OrgMemberStatus = "active" | "invited" | "suspended";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: OrgRole;
  status: OrgMemberStatus;
  created_at: string;
  updated_at: string;
}

export interface UserOrganization {
  organization: Organization;
  role: OrgRole;
  status: OrgMemberStatus;
}

export interface CreateOrganizationInput {
  name: string;
  slug?: string;
}
