import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
  CrosshairMode,
  type CandlestickData,
  type LineData,
  type Time,
  CandlestickSeries,
  LineSeries,
  createSeriesMarkers,
} from "lightweight-charts";
import type { StrategyResponse } from "../types";

interface ChartProps {
  data: StrategyResponse;
}

export default function Chart({ data }: ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#0d1117" },
        textColor: "#c9d1d9",
      },
      grid: {
        vertLines: { color: "#21262d" },
        horzLines: { color: "#21262d" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "#30363d",
      },
      timeScale: {
        borderColor: "#30363d",
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartContainerRef.current.clientWidth,
      height: 500,
    });

    chartRef.current = chart;

    // Candlestick series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderUpColor: "#26a69a",
      borderDownColor: "#ef5350",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    const candleData: CandlestickData[] = data.candles.map((c) => ({
      time: c.timestamp as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candlestickSeries.setData(candleData);

    // Bollinger Bands
    const bbUpperSeries = chart.addSeries(LineSeries, {
      color: "rgba(33, 150, 243, 0.5)",
      lineWidth: 1,
      title: "BB Upper",
    });

    const bbMiddleSeries = chart.addSeries(LineSeries, {
      color: "rgba(33, 150, 243, 0.3)",
      lineWidth: 1,
      lineStyle: 2,
      title: "BB Middle",
    });

    const bbLowerSeries = chart.addSeries(LineSeries, {
      color: "rgba(33, 150, 243, 0.5)",
      lineWidth: 1,
      title: "BB Lower",
    });

    const bbUpperData: LineData[] = [];
    const bbMiddleData: LineData[] = [];
    const bbLowerData: LineData[] = [];

    data.indicators.forEach((ind) => {
      if (ind.bb_upper !== null) {
        bbUpperData.push({ time: ind.timestamp as Time, value: ind.bb_upper });
      }
      if (ind.bb_middle !== null) {
        bbMiddleData.push({
          time: ind.timestamp as Time,
          value: ind.bb_middle,
        });
      }
      if (ind.bb_lower !== null) {
        bbLowerData.push({ time: ind.timestamp as Time, value: ind.bb_lower });
      }
    });

    bbUpperSeries.setData(bbUpperData);
    bbMiddleSeries.setData(bbMiddleData);
    bbLowerSeries.setData(bbLowerData);

    // VWAP
    const vwapSeries = chart.addSeries(LineSeries, {
      color: "#ff9800",
      lineWidth: 2,
      title: "VWAP",
    });

    const vwapData: LineData[] = [];
    data.indicators.forEach((ind) => {
      if (ind.vwap !== null) {
        vwapData.push({ time: ind.timestamp as Time, value: ind.vwap });
      }
    });
    vwapSeries.setData(vwapData);

    // EMA 200 (horizontal line from 15m)
    if (data.ema_200_15m !== null) {
      const emaSeries = chart.addSeries(LineSeries, {
        color: "#e040fb",
        lineWidth: 2,
        lineStyle: 2,
        title: "EMA 200 (15m)",
      });

      const emaData: LineData[] = data.candles.map((c) => ({
        time: c.timestamp as Time,
        value: data.ema_200_15m!,
      }));
      emaSeries.setData(emaData);
    }

    // Signal markers
    const markers = data.signals.map((signal) => ({
      time: signal.timestamp as Time,
      position: signal.signal_type === "buy" ? ("belowBar" as const) : ("aboveBar" as const),
      color: signal.signal_type === "buy" ? "#26a69a" : "#ef5350",
      shape: signal.signal_type === "buy" ? ("arrowUp" as const) : ("arrowDown" as const),
      text: signal.signal_type === "buy" ? "BUY" : "SELL",
    }));

    createSeriesMarkers(candlestickSeries, markers);

    // Fit content
    chart.timeScale().fitContent();

    // Resize handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data]);

  return (
    <div
      ref={chartContainerRef}
      style={{ width: "100%", position: "relative" }}
    />
  );
}
