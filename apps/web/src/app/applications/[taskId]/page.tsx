import { Live } from "@/components/Live";
import { getApplication } from "@/lib/api";

type Params = { taskId: string };

export default async function Page({ params }: { params: Promise<Params> }) {
  const { taskId } = await params;
  const initial = await getApplication(taskId);

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
      <Live initial={initial} />
    </main>
  );
}
