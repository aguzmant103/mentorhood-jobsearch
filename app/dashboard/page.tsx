import Image from "next/image";
import { JobSearchDashboard } from "@/components/job-search-dashboard";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="fixed top-6 left-6">
        <Image
          src="/mentorhood.jpeg"
          alt="Mentorhood logo"
          width={60}
          height={60}
          className="rounded-lg"
          priority
        />
      </div>

      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex flex-col items-center gap-4 mb-8">
          <h1 className="text-2xl font-bold">Panel de Búsqueda</h1>
          <p className="text-muted-foreground">Sube tu CV y encuentra roles remotos</p>
        </div>
        <div className="max-w-4xl mx-auto px-4">
          <JobSearchDashboard />
        </div>
      </div>
    </main>
  );
} 