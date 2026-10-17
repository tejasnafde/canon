import { useEffect } from 'react'

/** "Canon: <page>", or the plain product line on home. */
export function useTitle(page?: string) {
  useEffect(() => {
    document.title = page ? `Canon: ${page}` : 'Canon: the shared memory of a company'
  }, [page])
}
