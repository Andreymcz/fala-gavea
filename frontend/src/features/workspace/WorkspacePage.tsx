import { lazy, Suspense, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { useWorkspaceStore, defaultViewsForRole } from '@/store/workspaceStore'
import { FilterPanel } from './FilterPanel'
import { ViewToggleBar } from './ViewToggleBar'

const MapView = lazy(() => import('./views/MapView').then((m) => ({ default: m.MapView })))
const TableView = lazy(() => import('./views/TableView').then((m) => ({ default: m.TableView })))
const TopicsView = lazy(() => import('./views/TopicsView').then((m) => ({ default: m.TopicsView })))
const SimilarsView = lazy(() =>
  import('./views/SimilarsView').then((m) => ({ default: m.SimilarsView })),
)
const ChatView = lazy(() => import('./views/ChatView').then((m) => ({ default: m.ChatView })))
const CestaView = lazy(() => import('./views/CestaView').then((m) => ({ default: m.CestaView })))

export function WorkspacePage() {
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const activeViews = useWorkspaceStore((s) => s.activeViews)
  const isDirty = useWorkspaceStore((s) => s.isDirty())
  const setDraftFilter = useWorkspaceStore((s) => s.setDraftFilter)
  const applyFilters = useWorkspaceStore((s) => s.applyFilters)

  // Apply "Meus relatos" filter when navigated via ?meus_relatos=1
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    if (params.get('meus_relatos') === '1' && user) {
      setDraftFilter({ author_id: user.id })
      applyFilters()
      navigate('/', { replace: true })
    }
  }, []) // intentional: run once on mount only

  // Initialize views for role on mount (only once per role change)
  useEffect(() => {
    const views = defaultViewsForRole(user?.role)
    useWorkspaceStore.setState({ activeViews: views })
  }, [user?.role])

  // Browser tab / window close guard
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty])

  return (
    <>
      <div className="flex flex-1 overflow-hidden h-full">
        {/* Left rail filter panel */}
        <FilterPanel />
        {/* Main area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <ViewToggleBar />
          {/* View grid — overflow-hidden so each view scrolls its own content
              (the table has its own internal scroll); keeps the map fixed in place */}
          <div className="flex flex-1 overflow-hidden gap-2 p-2">
            {activeViews.length === 0 && (
              <div className="flex items-center justify-center flex-1 text-gray-400 text-sm">
                Selecione uma visão acima.
              </div>
            )}
            {activeViews.map((viewId) => {
              if (viewId === 'map') {
                return (
                  <div key={viewId} className="flex flex-col flex-1 h-full min-h-[300px] min-w-[300px]">
                    <Suspense
                      fallback={
                        <div className="flex-1 min-h-[300px] bg-gray-100 animate-pulse rounded" />
                      }
                    >
                      <MapView />
                    </Suspense>
                  </div>
                )
              }
              if (viewId === 'table') {
                return (
                  <div key={viewId} className="flex-1 min-h-[300px]">
                    <Suspense
                      fallback={
                        <div className="flex-1 min-h-[300px] bg-gray-100 animate-pulse rounded" />
                      }
                    >
                      <TableView />
                    </Suspense>
                  </div>
                )
              }
              if (viewId === 'keywords') {
                return (
                  <div key={viewId} className="flex-1 min-h-[300px] min-w-[280px]">
                    <Suspense
                      fallback={
                        <div className="flex-1 min-h-[300px] bg-gray-100 animate-pulse rounded" />
                      }
                    >
                      <TopicsView />
                    </Suspense>
                  </div>
                )
              }
              if (viewId === 'similars') {
                return (
                  <div key={viewId} className="flex-1 min-h-[300px] min-w-[280px]">
                    <Suspense
                      fallback={
                        <div className="flex-1 min-h-[300px] bg-gray-100 animate-pulse rounded" />
                      }
                    >
                      <SimilarsView />
                    </Suspense>
                  </div>
                )
              }
              if (viewId === 'chat') {
                return (
                  <div key={viewId} className="flex-1 min-h-[300px] min-w-[280px]">
                    <Suspense
                      fallback={
                        <div className="flex-1 min-h-[300px] bg-gray-100 animate-pulse rounded" />
                      }
                    >
                      <ChatView />
                    </Suspense>
                  </div>
                )
              }
              if (viewId === 'cesta') {
                return (
                  <div key={viewId} className="flex-1 min-h-[300px] min-w-[280px]">
                    <Suspense
                      fallback={
                        <div className="flex-1 min-h-[300px] bg-gray-100 animate-pulse rounded" />
                      }
                    >
                      <CestaView />
                    </Suspense>
                  </div>
                )
              }
              // Fallback placeholder for unknown view ids
              return (
                <div
                  key={viewId}
                  className="flex items-center justify-center bg-gray-50 border border-gray-200 rounded-md text-gray-400 text-sm min-h-32 flex-1 basis-80"
                >
                  {viewId}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </>
  )
}
