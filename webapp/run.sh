#!/bin/bash

cd "$(dirname "$0")"

cd backend
cargo watch -x run &
pid=( "$!" )
cd ..

cd frontend
npm run dev

kill "$pid"