import Image from "next/image";
import { SignInWrapper } from "@/components/sign-in-wrapper";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full px-4">
        <div className="flex flex-col items-center gap-8 mb-8">
          <Image
            src="/mentorhood.jpeg"
            alt="Mentorhood logo"
            width={180}
            height={180}
            className="rounded-lg"
            priority
          />
          <div className="text-center">
            <h1 className="text-2xl font-bold">Bienvenido de nuevo</h1>
            <p className="text-muted-foreground mt-2">Inicia sesión en tu cuenta</p>
          </div>
        </div>
        <SignInWrapper />
      </div>
    </main>
  );
}
