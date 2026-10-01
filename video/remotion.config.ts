import { Config } from '@remotion/cli/config'

// H.264 for every browser, at a quality where the UI text stays crisp.
Config.setVideoImageFormat('jpeg')
Config.setJpegQuality(95)
Config.setCodec('h264')
Config.setCrf(20)
Config.setPixelFormat('yuv420p')
