import { Config } from '@remotion/cli/config'

// Frames as high quality JPEGs. The mp4 quality (--crf, yuv420p) is set in the
// package.json scripts, because the gallery GIF render rejects both.
Config.setVideoImageFormat('jpeg')
Config.setJpegQuality(95)
