import json
from typing import List
from typing import Optional
from typing import Union

import numpy as np
from plotly import graph_objs as go

from evidently.base_metric import InputData
from evidently.base_metric import Metric
from evidently.base_metric import MetricResult
from evidently.core import IncludeTags
from evidently.metric_results import raw_agg_properties
from evidently.metrics.regression_performance.objects import PredActualScatter
from evidently.metrics.regression_performance.objects import scatter_as_dict
from evidently.model.widget import BaseWidgetInfo
from evidently.options.base import AnyOptions
from evidently.renderers.base_renderer import MetricRenderer
from evidently.renderers.base_renderer import default_renderer
from evidently.renderers.html_widgets import header_text
from evidently.utils.data_operations import process_columns
from evidently.utils.visualizations import plot_scatter


class AggPredActualScatter(MetricResult):
    class Config:
        dict_include = False
        tags = {IncludeTags.Render}

    # todo
    data: dict


class RegressionPredictedVsActualScatterResults(MetricResult):
    class Config:
        dict_include = False
        tags = {IncludeTags.Render}

    current: Union[PredActualScatter, AggPredActualScatter]
    reference: Optional[Union[PredActualScatter, AggPredActualScatter]]

    current_raw, current_agg = raw_agg_properties("current", PredActualScatter, AggPredActualScatter, False)
    reference_raw, reference_agg = raw_agg_properties("reference", PredActualScatter, AggPredActualScatter, True)


class RegressionPredictedVsActualScatter(Metric[RegressionPredictedVsActualScatterResults]):
    def __init__(self, options: AnyOptions = None):
        super().__init__(options=options)

    def calculate(self, data: InputData) -> RegressionPredictedVsActualScatterResults:
        dataset_columns = process_columns(data.current_data, data.column_mapping)
        target_name = dataset_columns.utility_columns.target
        prediction_name = dataset_columns.utility_columns.prediction
        curr_df = data.current_data
        ref_df = data.reference_data
        if target_name is None or prediction_name is None:
            raise ValueError("The columns 'target' and 'prediction' columns should be present")
        if not isinstance(prediction_name, str):
            raise ValueError("Expect one column for prediction. List of columns was provided.")
        if not self.get_options().agg_data:
            curr_df = self._make_df_for_plot(curr_df, target_name, prediction_name, None)
            current_scatter = PredActualScatter(predicted=curr_df[prediction_name], actual=curr_df[target_name])
            reference_scatter: Optional[PredActualScatter] = None
            if data.reference_data is not None:
                ref_df = self._make_df_for_plot(ref_df, target_name, prediction_name, None)
                reference_scatter = PredActualScatter(predicted=ref_df[prediction_name], actual=ref_df[target_name])
            return RegressionPredictedVsActualScatterResults(current=current_scatter, reference=reference_scatter)

        current_agg = AggPredActualScatter(data={"a": 1, "b": 2})
        reference_agg = None
        if data.reference_data is not None:
            reference_agg = AggPredActualScatter(data={"a": 5, "b": 2})
        return RegressionPredictedVsActualScatterResults(current=current_agg, reference_agg=reference_agg)

    def _make_df_for_plot(self, df, target_name: str, prediction_name: str, datetime_column_name: Optional[str]):
        result = df.replace([np.inf, -np.inf], np.nan)
        if datetime_column_name is not None:
            result.dropna(
                axis=0,
                how="any",
                inplace=True,
                subset=[target_name, prediction_name, datetime_column_name],
            )
            return result.sort_values(datetime_column_name)
        result.dropna(axis=0, how="any", inplace=True, subset=[target_name, prediction_name])
        return result.sort_index()


@default_renderer(wrap_type=RegressionPredictedVsActualScatter)
class RegressionPredictedVsActualScatterRenderer(MetricRenderer):
    def render_raw(self, current: PredActualScatter, reference: Optional[PredActualScatter]):
        fig = plot_scatter(
            curr=scatter_as_dict(current),
            ref=scatter_as_dict(reference),
            x="actual",
            y="predicted",
            xaxis_name="Actual value",
            yaxis_name="Predicted value",
            color_options=self.color_options,
        )
        return [
            header_text(label="Predicted vs Actual"),
            BaseWidgetInfo(
                title="",
                size=2,
                type="big_graph",
                params={"data": fig["data"], "layout": fig["layout"]},
            ),
        ]

    def render_agg(self, current: AggPredActualScatter, reference: Optional[AggPredActualScatter]):
        # todo
        data = [go.Bar(x=list(current.data.keys()), y=list(current.data.values()))]
        if reference is not None:
            data.append(go.Bar(x=list(reference.data.keys()), y=list(reference.data.values())))
        fig_agg = go.Figure(data=data)
        fig_agg = json.loads(fig_agg.to_json())

        return [
            header_text(label="Predicted vs Actual"),
            BaseWidgetInfo(
                title="",
                size=2,
                type="big_graph",
                params={"data": fig_agg["data"], "layout": fig_agg["layout"]},
            ),
        ]

    def render_html(self, obj: RegressionPredictedVsActualScatter) -> List[BaseWidgetInfo]:
        result = obj.get_result()
        if obj.get_options().agg_data:
            return self.render_agg(result.current_agg, result.reference_agg)
        return self.render_raw(result.current_raw, result.reference_raw)
