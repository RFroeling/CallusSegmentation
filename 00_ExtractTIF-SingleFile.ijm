// ImageJ Macro to extract TIF files from LIF files using Bio-Formats
// Saves the TIF files in a new folder '01_tif' and logs actions

// ================== Functions ==================

// Function to check and create directory
function makeDir(dir) {
    if(!File.exists(dir)){
        File.makeDirectory(dir);
        print("Directory created: " + dir);
    } else {
        print("Found: " + dir);
    }
}

// Function to get current timestamp as string
function getTimestamp() {
    getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
    TimeString = "" + year;
    if (month<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+month+1;
    if(dayOfMonth<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+dayOfMonth+"_";
    if (hour<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+hour;
    if (minute<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+minute;
    if (second<10) {TimeString = TimeString+"0";}
    TimeString = TimeString+second;
    return TimeString;
}

// Function to create log file and write header
function createLogFile(logDir, lifName) {
    logTimestamp = getTimestamp();
    logFilename = logDir + File.separator + logTimestamp + "__" + lifName + ".csv";
    header = "lif_file,series_name,output_path,width,height,channels,slices,frames,export_time\n";
    File.saveString(header, logFilename);
    return logFilename;
}

function Dimensions(){
    getDimensions(width, height, channels, slices, frames);
    dimensions = newArray(width, height, channels, slices, frames);
    return dimensions;
}

// Function to append export info to log file
function logExport(logFilename, lifName, seriesName, outputPath, dimensions) {
    exportTime = getTimestamp();
    line = lifName + "," + seriesName + "," + outputPath + "," + dimensions[0] + "," + dimensions[1] + "," + dimensions[2] + "," + dimensions[3] + "," + dimensions[4] + "," + exportTime;
    File.append(line, logFilename);
}

// Function to split series and save
function SplitSeries(lifPath, i) {
    // Open the series
    run("Bio-Formats Importer", "open=[" + lifPath + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT series_" + i);
    
    // Split the channels (if it contains channels)
    dimensions = Dimensions();
    channels = dimensions[2];
    if (channels > 1) {
    	run("Make Substack...", "channels=1");
    }
    return dimensions;
}

// Function to save the series with a clean name
function SaveSeries(outputDir, logFilename, lifName) {
    // Get series title
    Ext.getSeriesName(seriesName);
    seriesName_arr = split(seriesName, "/");
    cleanSeriesName = seriesName_arr[lengthOf(seriesName_arr)-1];

    // Save the series as TIFF
    savePath = outputDir + File.separator + cleanSeriesName + ".tif";
    saveAs("Tiff", savePath);
    print("Saved to: " + savePath);

    // Log the export
    logExport(logFilename, lifName, cleanSeriesName, savePath, dimensions);

    // Close the image to free memory
    close("*");
}

// ================== Execution ==================

setBatchMode(true);

// File selection
lifPath = File.openDialog("Select LIF file");

// Directory management
lifDir = File.getDirectory(lifPath);
parentDir = File.getParent(lifDir);
outputDir = parentDir +  "/01_tif";
logDir = outputDir + "/logs";

// Check and create directories
makeDir(outputDir);
makeDir(logDir);

// Get LIF filename (without path)
lifNameArr = split(lifPath, File.separator);
lifName = lifNameArr[lengthOf(lifNameArr)-1];
lifName = replace(lifName, ".lif", "");

// Create log file
logFilename = createLogFile(logDir, lifName);

// Get the number of series in the LIF
run("Bio-Formats Macro Extensions");
Ext.setId(lifPath);
Ext.getSeriesCount(seriesCount);
print("Found " + seriesCount + " series in file.");

// Loop through each series
for (i = 0; i < seriesCount; i++) {
    // Set current series
    Ext.setSeries(i);
    dimensions = SplitSeries(lifPath, i);
    SaveSeries(outputDir, logFilename, lifName);
}

// Close Bio-Formats Macro Extensions
Ext.close();
print("All series processed.");

setBatchMode(false);