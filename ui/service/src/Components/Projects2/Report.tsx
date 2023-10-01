import { LoaderFunctionArgs, useLoaderData, useParams } from 'react-router-dom'
import invariant from 'tiny-invariant'
import { api } from '../../api/RemoteApi'
import { DashboardContent } from '../../lib/components/DashboardContent'
import DashboardContext, { CreateDashboardContextState } from '../../lib/contexts/DashboardContext'

export const loader = async ({ params }: LoaderFunctionArgs) => {
  const { projectId, reportId } = params

  invariant(projectId, 'missing projectId')
  invariant(reportId, 'missing reportId')

  return api.getDashboard(projectId, reportId)
}

export const Report = () => {
  const { projectId, reportId } = useParams()
  invariant(projectId, 'missing projectId')
  invariant(reportId, 'missing reportId')

  const data = useLoaderData() as Awaited<ReturnType<typeof loader>>

  return (
    <>
      <DashboardContext.Provider
        value={CreateDashboardContextState({
          getAdditionGraphData: (graphId) =>
            api.getAdditionalGraphData(projectId, reportId, graphId),
          getAdditionWidgetData: (widgetId) =>
            api.getAdditionalWidgetData(projectId, reportId, widgetId)
        })}
      >
        <DashboardContent info={data} />
      </DashboardContext.Provider>
    </>
  )
}
