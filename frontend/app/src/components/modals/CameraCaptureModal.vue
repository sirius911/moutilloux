<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ModalShell from '@/components/ui/ModalShell.vue'

const emit = defineEmits<{ close: []; captured: [file: File] }>()

type Phase = 'requesting' | 'live' | 'error' | 'captured'

const phase = ref<Phase>('requesting')
const stream = ref<MediaStream | null>(null)
const errorMessage = ref('')
const capturedBlob = ref<Blob | null>(null)
const capturedUrl = ref<string | null>(null)

const videoEl = ref<HTMLVideoElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)

function stopStream() {
  stream.value?.getTracks().forEach((t) => t.stop())
  stream.value = null
}

function revokeCapturedUrl() {
  if (capturedUrl.value) {
    URL.revokeObjectURL(capturedUrl.value)
    capturedUrl.value = null
  }
}

async function startCamera() {
  phase.value = 'requesting'
  errorMessage.value = ''
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: true })
    stream.value = s
    phase.value = 'live'
    if (videoEl.value) {
      videoEl.value.srcObject = s
    }
  } catch (e) {
    phase.value = 'error'
    const name = e instanceof DOMException ? e.name : ''
    if (name === 'NotAllowedError') {
      errorMessage.value = 'Permission caméra refusée.'
    } else if (name === 'NotFoundError') {
      errorMessage.value = 'Aucune caméra détectée.'
    } else {
      errorMessage.value = "Impossible d'accéder à la caméra."
    }
  }
}

function capture() {
  const video = videoEl.value
  const canvas = canvasEl.value
  if (!video || !canvas) return
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  canvas.toBlob((blob) => {
    if (!blob) return
    capturedBlob.value = blob
    revokeCapturedUrl()
    capturedUrl.value = URL.createObjectURL(blob)
    phase.value = 'captured'
  }, 'image/jpeg')
}

function retake() {
  revokeCapturedUrl()
  capturedBlob.value = null
  phase.value = 'live'
}

function useCapture() {
  if (!capturedBlob.value) return
  const file = new File([capturedBlob.value], 'capture.jpg', { type: 'image/jpeg' })
  stopStream()
  emit('captured', file)
  emit('close')
}

function close() {
  stopStream()
  emit('close')
}

onMounted(() => {
  startCamera()
})

onUnmounted(() => {
  stopStream()
  revokeCapturedUrl()
})
</script>

<template>
  <ModalShell title="Prendre une photo" subtitle="Cadrez le joueur puis capturez." size="sm" @close="close">
    <template #icon>
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
        <circle cx="12" cy="13" r="3.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </template>

    <div class="cam-body">
      <p v-if="phase === 'requesting'" class="cam-msg">Demande d'accès à la caméra…</p>

      <p v-else-if="phase === 'error'" class="cam-msg cam-msg-error">
        {{ errorMessage }}<br />
        Vous pouvez téléverser une photo depuis la modale précédente.
      </p>

      <div v-show="phase === 'live'" class="cam-preview">
        <video ref="videoEl" autoplay muted playsinline></video>
      </div>

      <div v-if="phase === 'captured'" class="cam-preview">
        <img v-if="capturedUrl" :src="capturedUrl" alt="Aperçu de la capture" />
      </div>

      <canvas ref="canvasEl" class="cam-canvas-hidden"></canvas>
    </div>

    <template #footer>
      <button class="adm-btn" type="button" @click="close">Annuler</button>
      <button v-if="phase === 'live'" class="adm-btn primary" type="button" @click="capture">
        Capturer
      </button>
      <template v-else-if="phase === 'captured'">
        <button class="adm-btn" type="button" @click="retake">Reprendre</button>
        <button class="adm-btn primary" type="button" @click="useCapture">Utiliser</button>
      </template>
    </template>
  </ModalShell>
</template>

<style scoped>
.cam-body {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cam-msg {
  margin: 0;
  font-size: 13px;
  color: var(--ink-2);
  text-align: center;
}

.cam-msg-error {
  color: var(--danger);
}

.cam-preview {
  width: 100%;
  aspect-ratio: 4 / 3;
  background: #000;
  border-radius: var(--r-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cam-preview video,
.cam-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cam-canvas-hidden {
  display: none;
}

.adm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  background: var(--bg-3);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-1);
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
  font-family: inherit;
}

.adm-btn:hover { background: var(--bg-4); }

.adm-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.adm-btn.primary:hover { opacity: 0.9; }
</style>
