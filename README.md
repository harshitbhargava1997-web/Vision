# Literacy Portal Literacy Portal — starter

A new, separate Next.js app for teachers and school leaders. It is independent of the existing Streamlit deployment and does not edit or replace it.

## What is in this starter

- App Router with TypeScript and responsive portal screens.
- Supabase email/password sign-in using cookie-based server-side sessions.
- Protected dashboard and sign-out.
- Initial navigation and literacy progression for Nursery, LKG, UKG, Grade 1 and Grade 2.
- Teacher readiness and student progress are presented as the two connected workstreams.

The dashboard is a signed-in shell, not a live assessment system yet. It deliberately does not read or write your existing tables until we review their exact schemas and access policies. It contains no production data and makes no database changes.

## Run locally

1. Install Node.js 20.9 or newer and npm.
2. In this directory, install dependencies: `npm install`.
3. Copy `.env.example` to `.env.local`.
4. Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` from the Supabase project's Connect / API settings. Use the publishable key; never put a service-role key in a `NEXT_PUBLIC_*` variable.
5. In Supabase Auth URL Configuration, add `http://localhost:3000` to Site URL / redirect URLs for local testing.
6. Create or enable a test user in Supabase Auth.
7. Run `npm run dev` and open `http://localhost:3000`.

## Deploy as a separate Vercel project

Push this folder to its own GitHub repository, import that repository into Vercel, select Next.js, then add the same two environment variables to the Vercel project. Add the Vercel deployment URL to Supabase Auth's allowed redirect URLs. Deploy first to a preview URL and test sign-in/sign-out before sharing it with staff. This does not affect Streamlit unless someone explicitly changes that deployment's configuration.

## Before connecting real records

Review the actual Supabase table definitions and RLS policies. Then agree the additive app tables for school membership, role (teacher, coordinator, principal, academic consultant, owner), class rosters, competency assessment results, and reviewer feedback. Every read/write path must be constrained by school membership in PostgreSQL RLS. Do not depend on hiding UI links for authorization. Preserve the existing `teacher_records` and `classroom_observations` data and policies; do not run the older Streamlit migration as part of this app setup.

## Project notes

- `proxy.ts` refreshes/verifies Supabase Auth cookies for the App Router.
- `src/app/actions.ts` contains server-side sign-in and sign-out actions.
- `src/lib/supabase/` contains separate server and proxy clients.
- No Supabase credentials are included in the project.

