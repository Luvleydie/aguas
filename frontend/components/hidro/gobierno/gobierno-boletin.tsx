import { BoletinView } from "@/components/hidro/boletin-view"
import { boletinActualReal } from "@/lib/boletin-real-mock"

export function GobiernoBoletin() {
  return <BoletinView boletin={boletinActualReal} showPublish />
}
