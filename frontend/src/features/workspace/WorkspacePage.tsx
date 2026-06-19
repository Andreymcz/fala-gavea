import { useEffect } from 'react'
import { useAuth } from '@/auth/AuthContext'
import { useWorkspaceStore, defaultViewsForRole } from '@/store/workspaceStore'
import { FilterPanel } from './FilterPanel'
import { ViewToggleBar } from './ViewToggleBar'

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
        <div className="flex flex-1 overflow-hidden gap-2 p-2 flex-wrap content-start">
          {activeViews.length === 0 && (
            <div className="flex items-center justify-center flex-1 text-gray-400 text-sm">
              Selecione uma visão acima.
            </div>
          )}
          {/* View placeholders — actual view components added in Steps 5-10 */}
          {activeViews.map((viewId) => (
            <div
              key={viewId}
              className="flex items-center justify-center bg-gray-50 border border-gray-200 rounded-md text-gray-400 text-sm min-h-32 flex-1 basis-80"
            >
              {viewId}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
