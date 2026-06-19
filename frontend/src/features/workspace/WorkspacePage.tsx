import { lazy, Suspense, useEffect } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { useWorkspaceStore, defaultViewsForRole } from '@/store/workspaceStore'
import { FilterPanel } from './FilterPanel'
import { ViewToggleBar } from './ViewToggleBar'

const MapView = lazy(() => import('./views/MapView').then((m) => ({ default: m.MapView })))

export function WorkspacePage() {
  const { user } = useAuth()
  const { activeViews } = useWorkspaceStore()

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
            // Placeholder for views added in later steps
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
  )
}
