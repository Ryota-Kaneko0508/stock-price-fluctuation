import styled from "styled-components";
import { LineChart } from '@mui/x-charts/LineChart';
import { Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogTitle from "@mui/material/DialogTitle";
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';

const today = new Date();
const formattedDate = today.toLocaleDateString('ja-JP', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit'
});

export const StockDetail = () => {
  const location = useLocation();
  const [dates, setDates] = useState<Date[]>([]);
  const [prices, setPrices] = useState<number[]>([]);
  const [status, setStatus] = useState(location.state.status);
  const tick = location.state.tick;
  const company = location.state.company;
  const [open, setOpen] = useState(false);
  const userId = localStorage.getItem("userID");

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  useEffect(() => {
    const endpoint = `http://localhost:8000/stocks/${tick}`;
    
    const offset = 10
    
    const query = {
      tick: tick,
      date: formattedDate,
      offset: offset
    }

    const headers = {
      "x-user-id": userId,
    };
    
    axios.get(endpoint, {params: query, headers: headers}).then((res) => {
      const dateObjects = res.data.dates.map((date: string) => {
        return new Date(date);
      });
      setDates(dateObjects);
      setPrices(res.data.prices);
      setStatus(res.data.status)
    });
    
  }, []);

  const handleToggleStatus = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newStatus = event.target.checked;
    const endpoint = `http://localhost:8000/stocks/${tick}`;
    const requestBody = {user_id: userId, status: newStatus}; 

    axios.patch(endpoint, requestBody).then((res) => {
      setStatus(res.data.status);
      console.log(res.data.status);
    }).catch((e) => {
      alert("該当する銘柄が見つかりませんでした");
    });
  }
  
  const chartProps = {
    xAxis: [{
      data: dates,
      scaleType: 'time' as const,
      tickNumber: 5,
      valueFormatter: (value: Date) => {
        const y = value.getFullYear();
        const m = value.getMonth() + 1;
        const d = value.getDate();
        const hh = value.getHours().toString().padStart(2, '0');
        const mm = value.getMinutes().toString().padStart(2, '0');
        return `${y}/${m}/${d} ${hh}:${mm}`;
      }
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
        <STitle>{tick}, {company}</STitle>
        <SButton onClick={handleOpen}>通知設定</SButton>
      </SHeaderContainer>
      <LineChart
        {...chartProps}
      />
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{tick}の通知設定</DialogTitle>
        <DialogActions style={{display: "flex", justifyContent: "center"}}>
          <FormGroup>
            <FormControlLabel control={<Switch checked={status} onChange={handleToggleStatus} />} label="通知" />
          </FormGroup>
        </DialogActions>
      </Dialog>
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