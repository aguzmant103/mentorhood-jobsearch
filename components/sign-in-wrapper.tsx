"use client";

import dynamic from 'next/dynamic';

const SignInForm = dynamic(
  () => import('@/components/sign-in-form').then(mod => mod.SignInForm),
  { ssr: false }
);

export function SignInWrapper() {
  return <SignInForm />;
} 