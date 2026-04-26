import { Live } from "@/components/Live";
import { getApplication } from "@/lib/api";

type Params = { taskId: string };

export default async function Page({ params }: { params: Promise<Params> }) {
  const { taskId } = await params;
  const initial = await getApplication(taskId);

  return <Live initial={initial} />;
}
