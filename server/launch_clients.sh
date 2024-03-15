declare -i counter=0
declare -i n_clients=2          #n (number)
declare -i limit_requests=10    #l (limit)
request_time_offset="4.0"       #w (wait)

rm ./client_requests_data/results/*

# Parse options
while [[ $# -gt 0 ]]; do
  case $1 in
    -n)
      n_clients="$2"
      shift
      shift
      ;;
    -l)
      limit_requests="$2"
      shift
      shift
      ;;
    -w)
      request_time_offset="$2"
      shift 
      shift
      ;;
    *)
      echo "Unknown arg: $(opt)"
      exit 1
  esac
done

# Print out the values of the options
echo "Launching ($n_clients) clients with parameters:"
echo "> limit_requests : $limit_requests"
echo "> max_holded_files : $max_holded_files"
echo "> request_time_offset : $request_time_offset"

while [[ counter -lt $n_clients ]]; do
  echo "launching client " $counter
  python3 auto_client.py $limit_requests $request_time_offset &
  ((counter++))
done