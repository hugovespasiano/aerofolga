export type Role = "admin" | "user";
export type Plan = "free" | "premium";
export type Status = "active" | "suspended";

export interface Profile {
  id: string;
  display_name: string | null;
  role: Role;
  plan: Plan;
  status: Status;
  permissions?: string[];
}
