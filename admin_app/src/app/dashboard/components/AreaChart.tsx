"use client";
import dynamic from "next/dynamic";

import { ApexOptions } from "apexcharts";

const ReactApexcharts = dynamic(() => import("react-apexcharts"), {
  ssr: false,
});

const AreaChart = ({ data, options }: { data: any; options: ApexOptions }) => {
  return (
    <div>
      <ReactApexcharts
        type="area"
        width="100%"
        height={450}
        options={options}
        series={data}
      />
    </div>
  );
};

export default AreaChart;
