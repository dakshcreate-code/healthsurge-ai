from src.forecast import NaiveSeasonalForecast, RegressionForecast

def test_naive_forecast():
    f = NaiveSeasonalForecast()
    history = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    # 12 months ago from month 13 (target_month) is history[13-12] = history[1] = 2?
    # Wait, if we have 13 items (0..12), the last item is for month 12.
    # So history[-12] is index 13 - 12 = 1. Value is 2.
    assert f.forecast(0, history, 13) == 2.0

def test_regression_forecast_non_negative():
    f = RegressionForecast()
    # A sharply decreasing sequence
    history = [100, 50, 10, 0, 0]
    pred = f.forecast(0, history, 5)
    assert pred >= 0.0
