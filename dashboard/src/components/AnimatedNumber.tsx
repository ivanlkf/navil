import { useEffect, useRef, useState } from 'react'

interface AnimatedNumberProps {
  value: number
  duration?: number
  formatFn?: (n: number) => string
  className?: string
}

export default function AnimatedNumber({ value, duration = 800, formatFn, className = '' }: AnimatedNumberProps) {
  const [display, setDisplay] = useState(0)
  const rafRef = useRef<number>(0)
  const startRef = useRef<number>(0)
  const fromRef = useRef(0)

  useEffect(() => {
    fromRef.current = display
    startRef.current = 0

    const animate = (ts: number) => {
      if (!startRef.current) startRef.current = ts
      const elapsed = ts - startRef.current
      const t = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3)
      const current = fromRef.current + (value - fromRef.current) * eased

      setDisplay(Math.round(current))

      if (t < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, duration])

  return (
    <span className={className}>
      {formatFn ? formatFn(display) : display}
    </span>
  )
}
