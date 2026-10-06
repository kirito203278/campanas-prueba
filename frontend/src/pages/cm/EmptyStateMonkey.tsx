import { useEffect, useRef, useState } from 'react'

const CONFETTI_COLORS = ['#5f37a3', '#7c4de0', '#ffde00', '#ff6a1a', '#4b2a82']

function launchConfetti() {
  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.inset = '0'
  container.style.pointerEvents = 'none'
  container.style.zIndex = '200'
  document.body.appendChild(container)

  for (let i = 0; i < 60; i++) {
    const piece = document.createElement('div')
    piece.className = 'confetti-piece'
    piece.style.left = `${Math.random() * 100}vw`
    piece.style.background = CONFETTI_COLORS[i % CONFETTI_COLORS.length]
    piece.style.animationDuration = `${1.4 + Math.random() * 1.2}s`
    piece.style.animationDelay = `${Math.random() * 0.3}s`
    container.appendChild(piece)
  }
  setTimeout(() => container.remove(), 3000)
}

function triggerWave() {
  const targets = document.querySelectorAll<HTMLElement>('.cm-sidebar-item, .cm-main-wave-target, .cm-sidebar-header, .empty-monkey-card')
  targets.forEach((el, i) => {
    el.style.animation = 'none'
    // forzar reflow para poder reiniciar la animación
    void el.offsetHeight
    el.style.animationDelay = `${i * 40}ms`
    el.classList.add('wave-fx')
    setTimeout(() => {
      el.classList.remove('wave-fx')
      el.style.animationDelay = ''
    }, 700 + i * 40)
  })
}

export default function EmptyStateMonkey({ onAddClick, onFullyAwake }: {
  onAddClick: () => void
  onFullyAwake: () => void
}) {
  const [hovering, setHovering] = useState(false)
  const [clicks, setClicks] = useState(0)
  const [stretching, setStretching] = useState(false)
  const typedBuffer = useRef('')

  const awake = clicks > 0
  const fullyAwake = clicks >= 5

  useEffect(() => {
    if (fullyAwake) {
      launchConfetti()
      onFullyAwake()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullyAwake])

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key.length !== 1) return
      typedBuffer.current = (typedBuffer.current + e.key.toLowerCase()).slice(-20)
      if (typedBuffer.current.endsWith('innquietus')) {
        triggerWave()
        typedBuffer.current = ''
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  function handleClick() {
    setClicks((c) => c + 1)
    setStretching(true)
    setTimeout(() => setStretching(false), 400)
  }

  const eyesOpen = awake || hovering

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 420, textAlign: 'center', gap: 18 }}>
      <div
        className="empty-monkey-card"
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
        onClick={handleClick}
        style={{
          cursor: 'pointer',
          userSelect: 'none',
          transform: stretching ? 'scale(1.08) translateY(-6px)' : 'scale(1)',
          transition: 'transform 0.35s cubic-bezier(.34,1.56,.64,1)',
        }}
        title="🙈"
      >
        <svg width="140" height="140" viewBox="0 0 140 140" fill="none">
          <ellipse cx="70" cy="118" rx="34" ry="8" fill="#000" opacity="0.06" />
          {/* orejas */}
          <circle cx="30" cy="55" r="18" fill="#6b4a2f" />
          <circle cx="110" cy="55" r="18" fill="#6b4a2f" />
          <circle cx="30" cy="55" r="10" fill="#c9967a" />
          <circle cx="110" cy="55" r="10" fill="#c9967a" />
          {/* cabeza */}
          <circle cx="70" cy="65" r="46" fill="#8a5a35" />
          {/* cara */}
          <ellipse cx="70" cy="76" rx="30" ry="26" fill="#e8c9a6" />

          {/* ojos */}
          {eyesOpen ? (
            <>
              <circle cx="57" cy="70" r="4.5" fill="#2b1c12">
                <animate attributeName="r" from="0.5" to="4.5" dur="0.18s" />
              </circle>
              <circle cx="83" cy="70" r="4.5" fill="#2b1c12">
                <animate attributeName="r" from="0.5" to="4.5" dur="0.18s" />
              </circle>
            </>
          ) : (
            <>
              <path d="M51 70 Q57 74 63 70" stroke="#2b1c12" strokeWidth="2.5" fill="none" strokeLinecap="round" />
              <path d="M77 70 Q83 74 89 70" stroke="#2b1c12" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            </>
          )}

          {/* nariz + boca */}
          <ellipse cx="70" cy="84" rx="9" ry="6" fill="#d9ab84" />
          <circle cx="66" cy="84" r="1.4" fill="#4a3323" />
          <circle cx="74" cy="84" r="1.4" fill="#4a3323" />
          {awake ? (
            <path d="M62 90 Q70 97 78 90" stroke="#4a3323" strokeWidth="2" fill="none" strokeLinecap="round" />
          ) : (
            <path d="M64 91 Q70 93 76 91" stroke="#4a3323" strokeWidth="2" fill="none" strokeLinecap="round" />
          )}

          {/* brazos: se estiran hacia arriba al hacer click */}
          <path
            d={stretching ? 'M32 100 Q10 70 20 40' : 'M32 100 Q22 108 28 118'}
            stroke="#6b4a2f" strokeWidth="10" fill="none" strokeLinecap="round"
            style={{ transition: 'd 0.35s ease' }}
          />
          <path
            d={stretching ? 'M108 100 Q130 70 120 40' : 'M108 100 Q118 108 112 118'}
            stroke="#6b4a2f" strokeWidth="10" fill="none" strokeLinecap="round"
            style={{ transition: 'd 0.35s ease' }}
          />

          {!awake && (
            <text x="104" y="34" fontSize="14" fill="var(--inn-purple-500)" fontWeight="700">z</text>
          )}
          {!awake && (
            <text x="114" y="24" fontSize="10" fill="var(--inn-purple-500)" fontWeight="700">z</text>
          )}
        </svg>
      </div>

      <div>
        <p style={{ margin: '0 0 4px', fontSize: 16, fontWeight: 600, color: 'var(--ink-900)' }}>
          {fullyAwake ? '¡Ya despertaste al INNquieto! Ahora despierta a tus clientes 🚀' : 'Aún no hay clientes ni campañas'}
        </p>
        {!fullyAwake && (
          <p style={{ margin: 0, color: 'var(--ink-500)', fontSize: 13 }}>
            Agrega tu primer cliente para empezar a capturar sus campañas.
          </p>
        )}
      </div>

      <button className={`btn btn-primary ${fullyAwake ? 'pulse-attention' : ''}`} onClick={onAddClick}>
        Agregar clientes
      </button>
    </div>
  )
}
