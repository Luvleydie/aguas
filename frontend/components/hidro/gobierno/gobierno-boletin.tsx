import { BoletinView } from "@/components/hidro/boletin-view"
import { boletinActual } from "@/lib/hidro-data"

export function GobiernoBoletin() {
  return <BoletinView boletin={boletinActual} showPublish />
}
