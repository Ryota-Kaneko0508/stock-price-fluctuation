import styled from "styled-components";
import { LineChart } from '@mui/x-charts/LineChart';
import { Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";

const today = new Date();
const formattedDate = today.toLocaleDateString('ja-JP', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit'
});

export const StockDetail = () => {
  const [times, setTimes] = useState<Date[]>([]);
  const [prices, setPrices] = useState<number[]>([]);

  const onClickSetting = () => {
    alert("test");
  };

  useEffect(() => {
    // あとでへんこうする
    const tick = "7203.T"
    const endpoint = "http://localhost:8000/stocks/" + tick;
    
    const offset = 20
    
    const query = {
      tick: tick,
      date: formattedDate,
      offset: offset
    }
    
    axios.get(endpoint, {params: query}).then((res) => {
      const dateObjects = res.data.times.map((t: string) => {
        const [hours, minutes] = t.split(':').map(Number);
        const d = new Date();
        d.setHours(hours, minutes, 0, 0);
        return d;
      });
      setTimes(dateObjects);
      setPrices(res.data.prices);
    });
    
  }, []);
  
  const chartProps = {
    xAxis: [{
      data: times,
      scaleType: 'time' as const,
      valueFormatter: (value: Date) => 
        value.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
    }],
    yAxis: [{label: "株価"}],
    series: [{ curve: 'linear' as const, data: prices }],
    height: 500,
  };

  if (!localStorage.getItem("userID")) {
    return <Navigate to = "/" />
  }

  return (
    <SWrapper>
      <SHeaderContainer>
        <STitle>{"7203.T"}, {"Toyota Motor Corporation"} <br />
          {formattedDate}
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