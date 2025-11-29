shopt -s nullglob
zipfiles=(${WATCH_DIR}/*.zip)
peakloadfiles=(${WATCH_DIR}/peakload_*)

if [ ${#zipfiles[@]} -eq 0 ] && [ ${#peakloadfiles[@]} -eq 0 ]; then
    echo "No zip or peak load files found in ${WATCH_DIR}"
    exit 0
fi
echo "Found ${#zipfiles[@]} zip file(s) to import"
echo "Found ${#peakloadfiles[@]} zip file(s) to import"

# tindeq custom sessions
for zipfile in "${zipfiles[@]}"; do
    echo "Importing: $zipfile"

    # Detect if it's a batch export by filename
    if [[ "$(basename "$zipfile")" == *"batch_export"* ]]; then
        ${TINDEQ} --storage-dir "$STORAGE_DIR" import --batch "$zipfile" $DELETE_APPENDIX
    else
        ${TINDEQ} --storage-dir "$STORAGE_DIR" import "$zipfile" $DELETE_APPENDIX
    fi

    if [ $? -eq 0 ]; then
        echo "Successfully imported: $zipfile"
    else
        echo "Failed to import: $zipfile"
    fi
done

for peakloadfile in "${peakloadfiles[@]}"; do
    echo "Importing: $peakloadfile"

    ${TINDEQ} --storage-dir "$STORAGE_DIR" peakload import "$peakloadfile"

    if [[ ${SHOULD_DELETE} == "1" ]]; then
        rm $peakloadfile
    fi

    if [ $? -eq 0 ]; then
        echo "Successfully imported: $peakloadfile"
    else
        echo "Failed to import: $peakloadfile"
    fi
done
