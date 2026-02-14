import * as React from "react";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import styled from "styled-components";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import { Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";

interface Column {
  id: "tick" | "company" | "price_yesterday" | "price_today" | "diff";
  label: string;
  minWidth?: number;
  align?: "right";
  priceFormat?: (value: number, currency: string) => string;
  format?: (value: number) => string;
}

const columns: readonly Column[] = [
  { id: "tick", label: "銘柄", minWidth: 170 },
  { id: "company", label: "社名", minWidth: 100 },
  {
    id: "price_yesterday",
    label: "終値",
    minWidth: 170,
    align: "right",
    priceFormat: (value: number, currency: string) =>
      value.toLocaleString("ja-JP", { style: "currency", currency: currency })
  },
  {
    id: "price_today",
    label: "株価",
    minWidth: 170,
    align: "right",
    priceFormat: (value: number, currency: string) =>
      value.toLocaleString("ja-JP", { style: "currency", currency: currency }),
  },
  {
    id: "diff",
    label: "差分",
    minWidth: 170,
    align: "right",
    format: (value: number) =>
      (value > 0 ? "+" : "") + value.toLocaleString("ja-JP"),
  },
];

interface Data {
  tick: string;
  company: string;
  currency: string;
  status: boolean;
  price_yesterday: number;
  price_today: number;
  diff: number;
}

function createData(
  tick: string,
  company: string,
  currency: string,
  status: boolean,
  price_yesterday: number,
  price_today: number,
): Data {
  const diff = price_today - price_yesterday;
  return { tick, company, currency, status, price_yesterday, price_today, diff };
}

export const StockList = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [stocks, setStocks] = useState<Data[]>([]);
  const [inputStock, setInputStock] = useState("");
  const [open, setOpen] = useState(false);
  const userId = localStorage.getItem("userID");

  const fetchStocks = () => {
    const endpoint = "http://localhost:8000/stocks";
  
    const headers = {
      headers: {
        "x-user-id": userId,
      },
    };
  
    axios.get(endpoint, headers).then((res) => {
      const datas = res.data.map((item: any) => {
        console.log(item.currency);
        return createData(
          item.tick,
          item.company,
          item.currency,
          item.status,
          item.price_yesterday,
          item.price_today,
        );
      });
      setStocks(datas);
    });
  }

  useEffect(() => {
    fetchStocks();
  }, []);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const onChangeInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInputStock(event.target.value);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  const onClickAdd = () => {
    const endpoint = `http://localhost:8000/stocks/${inputStock}`;
    const requestBody = {user_id: userId, tick: inputStock}; 

    axios.post(endpoint, requestBody).then((res) => {
      setOpen(false);
      alert("登録が完了しました！");
      setInputStock("");
      fetchStocks();

    }).catch((e) => {
      alert("該当する銘柄が見つかりませんでした");
    });

  };

  const onClickTableRow = (row: Data) => {
    navigate("/stocks/detail", {
      state: {
        tick: row.tick,
        company: row.company,
        status: row.status
      }
    });
  };

  if (!localStorage.getItem("userID")) {
    return <Navigate to="/" />;
  }

  return (
    <SWrapper>
      <SHeaderContainer>
        <STitle>株価一覧</STitle>
        <SButton onClick={handleOpen}>+ 追加する</SButton>
      </SHeaderContainer>
      <Paper sx={{ width: "100%", overflow: "hidden" }}>
        <TableContainer sx={{ maxHeight: 440 }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell
                    key={column.id}
                    align={column.align}
                    style={{ minWidth: column.minWidth }}
                  >
                    {column.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {stocks
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((row) => {
                  return (
                    <TableRow
                      hover
                      role="checkbox"
                      tabIndex={-1}
                      key={row.company}
                      onClick={() => onClickTableRow(row)}
                      style={{ cursor: "pointer" }}
                    >
                      {columns.map((column) => {
                        const value = row[column.id];

                        let displayValue = value;
                        if (typeof value === "number") {
                            if (column.priceFormat) {
                              displayValue = column.priceFormat(value, row.currency);
                            } else if (column.format) {
                              displayValue = column.format(value);
                            }
                        }

                        let textColor = "inherit";

                        if (column.id === "diff") {
                          if (row.diff > 0) textColor = "green";
                          if (row.diff <= 0) textColor = "red";
                        }
                        return (
                          <TableCell
                            key={column.id}
                            align={column.align}
                            style={{ color: textColor }}
                          >
                            {displayValue}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[10, 25, 100]}
          component="div"
          count={stocks.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>銘柄の購読追加</DialogTitle>
        <DialogContent>
          <DialogContentText>
            追加したい銘柄のID（Tickコード）を入力してください。
          </DialogContentText>
          <TextField
            autoFocus
            required
            margin="dense"
            id="name"
            name="tick"
            label="銘柄ID (例: 7203.T)"
            onChange={onChangeInput}
            fullWidth
            variant="standard"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>キャンセル</Button>
          <Button onClick={onClickAdd}>追加</Button>
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
