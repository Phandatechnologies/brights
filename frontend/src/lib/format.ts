export const formatRand = (amount: number) => `R${amount.toLocaleString('en-ZA')}`

/** [8, 9, 10] → "Grades 8–10"; [8, 12] → "Grades 8, 12"; [10] → "Grade 10" */
export function gradeRange(grades: number[]): string {
  if (grades.length === 0) return ''
  if (grades.length === 1) return `Grade ${grades[0]}`
  const contiguous = grades.every((g, i) => i === 0 || g === grades[i - 1] + 1)
  return contiguous && grades.length > 2
    ? `Grades ${grades[0]}–${grades[grades.length - 1]}`
    : `Grades ${grades.join(', ')}`
}

export function lessonModes(online: boolean, inPerson: boolean): string {
  if (online && inPerson) return 'Online and in person'
  return online ? 'Online' : 'In person'
}
