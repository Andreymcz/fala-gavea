import { lazy, Suspense, useEffect, useState } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { useWorkspaceStore, defaultViewsForRole } from '@/store/workspaceStore'
import { FilterPanel } from './FilterPanel'
import { ViewToggleBar } from './ViewToggleBar'
import { SelectionBar } from '@/features/map/SelectionBar'
import { CreateForwardingDialog } from '@/features/map/CreateForwardingDialog'

const MapView = lazy(() => import('./views/MapView').then((m) => ({ default: m.MapView })))
const TableView = lazy(() => import('./views/TableView').then((m) => ({ default: m.TableView })))
const TopicsView = lazy(() => import('./views/TopicsView').then((m) => ({ default: m.TopicsView })))
const SimilarsView = lazy(() =>
  import('./views/SimilarsView').then((m) => ({ default: m.SimilarsView })),
)
const ChatView = lazy(() => import('./views/ChatView').then((m) => ({ default: m.ChatView })))

export function WorkspacePage() {
  const { user } = useAuth()
  const { activeViews } = useWorkspaceStore()
  const { selectedIds, clearSelection } = useWorkspaceStore((s) => ({
    selectedIds: s.selectedIds,
    clearSelection: s.clearSelection,
  }))
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  const isAgent = user?.role === 'agent' || user?.role === 'admin'

  // Initialize views for role on mount (only once per role change)
  useEffect(() => {
    const views = defaultViewsForRole(user?.role)
    useWorkspaceStore.setState({ activeViews: views })
  }, [user?.role])

  return (
    <div className="flex flex-1 overflow-hidden h-full">
      {/* Left rail filter panel */}
      <FilterPanel />
      {/* Main area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <ViewToggleBar />
        {/* View grid */}
        <div className="flex flex-1 overflow-auto gap-2 p-2">
          {activeViews.length === 0 && (
            <div className="flex items-center justify-center flex-1 text-gray-400 text-sm">
              Selecione uma visão acima.
            </div>
          )}
          {activeViews.map((viewId) => {
            if (viewId === 'map') {
              return (
                <div key={viewId} className="flex-1 min-h-[300px] min-w-[300px]">
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
            if (viewId === 'topics') {
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
        {/* SelectionBar and CreateForwardingDialog — agents only */}
        {isAgent && (
          <>
            <SelectionBar
              count={selectedIds.size}
              onCreateForwarding={() => setShowCreateDialog(true)}
              onClear={clearSelection}
            />
            <CreateForwardingDialog
              open={showCreateDialog}
              selectedIds={Array.from(selectedIds)}
              onSuccess={clearSelection}
              onClose={() => setShowCreateDialog(false)}
            />
          </>
        )}
      </div>
    </div>
  )
}
