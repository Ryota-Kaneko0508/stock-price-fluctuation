import styled from "styled-components";
import { LineChart, LineChartProps } from '@mui/x-charts/LineChart';

const xlabel = [1, 2, 3, 5, 8, 10];

export const StockDetail = () => {
  const onClickSetting = () => {
    alert("test");
  };

  const chartProps = {
    xAxis: [{ data: xlabel }],
    series: [{ data: [2, 5.5, 2, 8.5, 1.5, 5] }],
    height: 500,
  };
  return (
    <SWrapper>
      <SHeaderContainer>
        <STitle>AAPL, Apple Inc <br />
          2016/01/12
        </STitle>
        <SButton onClick={onClickSetting}>通知設定</SButton>
      </SHeaderContainer>
      <LineChart
        {...chartProps}
      />
    </SWrapper>
  );
};

const SWrapper = styled.div`
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
`;

const SHeaderContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
`;

const STitle = styled.p`
  font-price_today: 20px;
`;

const SButton = styled.button`
  background-color: #11999e;
  color: #fff;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.3s;
  &:hover {
    opacity: 0.8;
  }
`;