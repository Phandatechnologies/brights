import type { Pathway } from '../api/tutor'

export const PATHWAYS: { value: Pathway; title: string; description: string }[] = [
  {
    value: 'academic',
    title: 'I passed Matric',
    description: "For matriculants, university students and graduates. You'll enter your Matric marks and can tutor subjects you passed with 60% or more.",
  },
  {
    value: 'teacher',
    title: "I'm a qualified teacher",
    description: "You'll provide your teaching qualification and SACE registration instead of Matric marks.",
  },
]
