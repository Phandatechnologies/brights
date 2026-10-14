import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <section className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-3xl font-bold text-brand-navy">Page not found</h1>
      <p className="mt-2 text-slate-600">The page you're looking for doesn't exist.</p>
      <Link to="/" className="mt-6 inline-block font-medium text-brand-blue hover:underline">Back to home</Link>
    </section>
  )
}
