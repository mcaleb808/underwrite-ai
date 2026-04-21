import { listApplications } from "@/lib/api";

import { RecentApplicationsList } from "./RecentApplicationsList";

export async function RecentApplications() {
  const items = await listApplications(20);
  if (items.length === 0) return null;
  return <RecentApplicationsList items={items} />;
}
