import React from "react";
import rows from "./rows";
import Grid from "@mui/material/Unstable_Grid2";
import Box from "@mui/material/Box";
import SwapVertIcon from "@mui/icons-material/SwapVert";
import TextField from "@mui/material/TextField";
import FilterAltOutlinedIcon from "@mui/icons-material/FilterAltOutlined";
import Pagination from "@mui/material/Pagination";
import Drawer from "@mui/material/Drawer";
import { ApexOptions } from "apexcharts";
import { appColors } from "@/utils/index";
import LineChart from "@/app/dashboard/components/LineChart";
import { getPerformancePageData } from "@/app/dashboard/api";
import { ApexData, Period } from "@/app/dashboard/types";
import { useAuth } from "@/utils/auth";
import { useEffect } from "react";

const N_TOP_CONTENT = 7;

interface PerformanceProps {
  timePeriod: Period;
}

const Performance: React.FC<PerformanceProps> = ({ timePeriod }) => {
  const { token } = useAuth();

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [timeseriesData, setTimeseriesData] = React.useState<ApexData[]>([]);
  const toggleDrawer = (newOpen: boolean) => () => {
    setDrawerOpen(newOpen);
  };

  useEffect(() => {
    if (token) {
      getPerformancePageData(timePeriod, token, N_TOP_CONTENT).then(
        (response) => {
          console.log(response.content_time_series);
          parseContentTimeSeries(response.content_time_series);
        },
      );
    } else {
      console.log("No token found");
    }
  }, [timePeriod, token]);

  const parseContentTimeSeries = (timeseriesData: Record<string, any>[]) => {
    const apexTimeSeriesData: ApexData[] = timeseriesData.map((series, idx) => {
      // const color =
      //  idx === 0 ? appColors.dashboardPrimary : appColors.dashboardLightGray;
      const zIndex = idx === 0 ? 3 : 2;
      const seriesData = {
        name: series.title,
        // color: color,
        zIndex: zIndex,
        data: Object.entries(series.query_count_time_series).map(
          ([period, queryCount]) => {
            const date = new Date(period);
            return {
              x: String(date),
              y: queryCount as number,
            };
          },
        ),
      };
      return seriesData;
    });
    console.log(apexTimeSeriesData);
    setTimeseriesData(apexTimeSeriesData);
  };

  const timeseriesOptions: ApexOptions = {
    title: {
      text: `Top content in the last ${timePeriod}`,
      align: "left",
      style: {
        fontSize: "25px",
        fontWeight: 400,
        color: appColors.black,
      },
    },
    chart: {
      id: "content-performance-timeseries",
      stacked: false,
    },
    dataLabels: {
      enabled: false,
    },
    xaxis: {
      type: "datetime",
      labels: {
        datetimeUTC: false,
      },
    },
    yaxis: {
      tickAmount: 5,
      labels: {
        formatter: function (value) {
          return String(Math.round(value)); // Format labels to show whole numbers
        },
      },
    },
    legend: {
      show: false,
      position: "top",
      horizontalAlign: "left",
    },
    stroke: {
      width: [3, ...Array(N_TOP_CONTENT).fill(3)],
      curve: "smooth",
      dashArray: [0, ...Array(N_TOP_CONTENT).fill(7)],
    },
    colors: appColors.dashboardBlueShades,
  };

  return (
    <>
      <Drawer open={drawerOpen} onClose={toggleDrawer(false)} anchor="right">
        <Box
          sx={{ width: 450 }}
          role="presentation"
          onClick={toggleDrawer(false)}
        >
          Feedback + AI Summary
        </Box>
      </Drawer>
      <Box
        bgcolor="white"
        sx={{
          height: 300,
          maxWidth: 1387,
          border: 0,
          padding: 2,
        }}
      >
        <LineChart options={timeseriesOptions} data={timeseriesData} />
      </Box>
      <Grid
        container
        columns={14}
        sx={{ mt: 3, maxWidth: 1387 }}
        columnSpacing={{ xs: 0 }}
      >
        <Grid
          container
          spacing={2}
          md={14}
          columns={14}
          sx={{
            border: 1,
            borderColor: "secondary.main",
            mt: 3,
            fontSize: "small",
            fontWeight: 700,
          }}
        >
          <Grid md={6}>Content Title</Grid>
          <Grid md={2}>Daily Average Sent</Grid>
          <Grid md={2}>Upvotes</Grid>
          <Grid md={2}>Downvotes</Grid>
          <Grid md={2}>Trend</Grid>
        </Grid>
        <Grid
          container
          spacing={2}
          md={14}
          columns={14}
          sx={{
            border: 1,
            borderTop: 0,
            borderColor: "secondary.main",
            mt: 1,
            fontSize: "small",
            fontWeight: 300,
            color: "text.secondary",
          }}
        >
          <Grid xs={6} sx={{ height: 20 }}>
            <TextField
              id="content-search"
              placeholder="Search"
              size="small"
              sx={{
                width: "90%",
                mt: -0.4,
                maxHeight: 20,
                marginRight: 1,
                bgcolor: "white",
                "& .MuiOutlinedInput-root": {},
              }}
              margin="none"
              inputProps={{
                style: {
                  height: 30,
                  backgroundColor: "white",
                  padding: "0 14px",
                },
              }}
            />
            <FilterAltOutlinedIcon fontSize="small" sx={{ fontWeight: 300 }} />
          </Grid>
          <Grid xs={2} display="flex" alignItems="center">
            <SwapVertIcon />
            Sort
          </Grid>
          <Grid xs={2} display="flex" alignItems="center">
            <SwapVertIcon />
            Sort
          </Grid>
          <Grid xs={2} display="flex" alignItems="center">
            <SwapVertIcon />
            Sort
          </Grid>
          <Grid xs={2} display="flex" alignItems="center">
            <SwapVertIcon />
            Sort
          </Grid>
        </Grid>

        {rows.map((row) => (
          <Grid
            key={row.id}
            container
            spacing={2}
            md={14}
            columns={14}
            onClick={toggleDrawer(true)}
            sx={{
              border: 1,
              borderTop: 0,
              borderColor: "secondary.main",
              borderBottomColor: "grey.300",
              bgcolor: "white",
              mt: 1,
              fontSize: "small",
              fontWeight: 300,
              "&:hover": { boxShadow: 2, zIndex: "1000" },
            }}
          >
            <Grid md={6}>{row.title}</Grid>
            <Grid md={2}>{row.totalSent}</Grid>
            <Grid md={2}>{row.totalUpvotePercentage}</Grid>
            <Grid md={2}>{row.totalDownvotePercentage}</Grid>
            <Grid md={2}>[TRENDLINE]</Grid>
          </Grid>
        ))}
        <Box
          justifyContent="center"
          justifySelf={"center"}
          alignItems="center"
          sx={{
            display: "flex",
            flexDirection: "row",
            flexGrow: 1,
            mt: 3,
          }}
        >
          <Pagination count={10} />
        </Box>
      </Grid>
    </>
  );
};

export default Performance;
