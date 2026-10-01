// The Calnio logo, the same paths as frontend/src/components/CalnioMark.vue.
export function Mark({ plate = '#0a0a0a', glyph = '#ffffff' }: { plate?: string; glyph?: string }) {
  return (
    <svg viewBox="0 0 240 240" style={{ display: 'block', width: '100%', height: '100%' }}>
      <rect width="240" height="240" rx="54" fill={plate} />
      <path
        d="M163.1,158.8 A58,58 0 1 1 163.1,81.2"
        fill="none"
        stroke={glyph}
        strokeWidth="26"
        strokeLinecap="round"
      />
      <rect x="148" y="108" width="24" height="24" rx="7" fill={glyph} />
    </svg>
  )
}
