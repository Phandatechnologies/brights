import type { TutorApplication } from '../../api/tutor'
import { PATHWAYS } from '../../lib/pathways'

function gradeRange(grades: number[]): string {
  if (grades.length === 0) return '—'
  const contiguous = grades.every((g, i) => i === 0 || g === grades[i - 1] + 1)
  return contiguous && grades.length > 2 ? `Grades ${grades[0]}–${grades[grades.length - 1]}` : `Grade${grades.length > 1 ? 's' : ''} ${grades.join(', ')}`
}

/** Read-only overview of an application, used on the review step and the status page. */
export function ApplicationSummary({ application }: { application: TutorApplication }) {
  // Subject decisions only mean something once the application has been decided.
  const showDecisions = ['approved', 'suspended'].includes(application.status)
  const pathway = PATHWAYS.find((p) => p.value === application.pathway)
  return (
    <dl className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-surface">
      <div className="p-5">
        <dt className="text-sm text-slate-500">Application type</dt>
        <dd className="mt-1 font-medium text-slate-900">{pathway?.title}</dd>
        {application.pathway === 'teacher' && (
          <dd className="mt-1 text-sm text-slate-700">
            {application.qualification_name || 'Qualification not entered'}
            <br />
            SACE number: {application.sace_number || 'not entered'}
          </dd>
        )}
      </div>
      <div className="p-5">
        <dt className="text-sm text-slate-500">Subjects</dt>
        <dd className="mt-2">
          {application.subjects.length === 0 ? (
            <span className="text-slate-500">None added</span>
          ) : (
            <ul className="space-y-1.5">
              {application.subjects.map((s) => (
                <li key={s.id} className="text-slate-900">
                  <div className="flex flex-wrap justify-between gap-x-4">
                    <span>
                      {s.subject.name}
                      {s.matric_mark !== null && <span className="ml-2 tabular-nums text-slate-500">{s.matric_mark}%</span>}
                      {showDecisions && s.decision !== 'pending' && (
                        <span className={`ml-2 inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${
                          s.decision === 'approved' ? 'bg-brand-teal/15 text-pass' : 'bg-brand-orange/10 text-below'
                        }`}>
                          {s.decision === 'approved' ? 'Approved' : 'Not approved'}
                        </span>
                      )}
                    </span>
                    <span className="text-slate-600">{gradeRange(s.grades)}</span>
                  </div>
                  {showDecisions && s.decision === 'declined' && s.decision_note && (
                    <p className="mt-0.5 text-sm text-slate-600">{s.decision_note}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </dd>
      </div>
      <div className="p-5">
        <dt className="text-sm text-slate-500">Documents</dt>
        <dd className="mt-2">
          {application.documents.length === 0 ? (
            <span className="text-slate-500">None uploaded</span>
          ) : (
            <ul className="space-y-1 text-slate-900">
              {application.documents.map((d) => (
                <li key={d.id}><span className="text-slate-500">{d.kind_label}:</span> {d.original_name}</li>
              ))}
            </ul>
          )}
        </dd>
      </div>
    </dl>
  )
}
