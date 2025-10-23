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
    TimeString = "" + year + "-";
    month = month+1; // From index to month number
    if (month<10) {TimeString = TimeString+"0";}
    TimeString = TimeString + month + "-";
    if(dayOfMonth<10) {TimeString = TimeString+"0";}
    TimeString = TimeString + dayOfMonth + " ";
    if (hour<10) {TimeString = TimeString+"0";}
    TimeString = TimeString + hour + ":";
    if (minute<10) {TimeString = TimeString+"0";}
    TimeString = TimeString + minute + ":";
    if (second<10) {TimeString = TimeString+"0";}
    TimeString = TimeString + second;
    return TimeString;
}

// Function to create log file and write header
function createLogFile(logFilename) {
    header = "Filename,Timestamp,Series,Exported\n";
    File.saveString(header, logFilename);
    print("Log file created: " + logFilename);
}

function Dimensions(){
    getDimensions(width, height, channels, slices, frames);
    dimensions = newArray(width, height, channels, slices, frames);
    return dimensions;
}

// Function to append export info to log file
function logExport(logFilename, lifName, seriesCount, exportCount) {
    exportTime = getTimestamp();
    line = lifName + "," + exportTime + "," + seriesCount + "," + exportCount;
    File.append(line, logFilename);
}

// Function to split series and save
function SplitSeries(lifPath, i) {
    // Open the series
    run("Bio-Formats Importer", "open=[" + lifPath + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT series_" + i+1);
    
    // Split the channels (if it contains channels)
    dimensions = Dimensions();
    channels = dimensions[2];
    if (channels > 1) {
    	run("Split Channels");
    	}
    return dimensions;
}

// Function to save the series with a clean name
function SaveSeries(outputDir, lifName, exportCount, i) {
    channels = getList("image.titles"); // List of all open channels
    
    // Get series title
    Ext.getSeriesName(seriesName);
    seriesName_arr = split(seriesName, "/");
    cleanSeriesName = seriesName_arr[lengthOf(seriesName_arr)-1];
 // Might be cause for weird naming
	
	// Save each open channel
	for (j = 0; j < channels.length; j++) {
    	selectImage(channels[j]);
	
    	// Save the series as TIFF
    	savePath = outputDir + File.separator + cleanSeriesName + "_C" + (j+1) + ".tif";
    	saveAs("Tiff", savePath);
    	print("Saving series " + (i+1) + ": " + cleanSeriesName + "_C" + (j+1) + ".tif");
        
        // Bookkeeping: count exports
        exportCount = exportCount + 1;

    	// Close the image to free memory
    	close();
    }
    return exportCount;    
}


// ================== Execution ==================

setBatchMode(true);

// File selection
lifPath = File.openDialog("Select LIF file");

// Directory management
lifDir = File.getDirectory(lifPath);
parentDir = File.getParent(lifDir);
outputDir = parentDir +  "/01_tif";
logDir = parentDir + "/_logs";

// Check and create directories
makeDir(outputDir);
makeDir(logDir);

// Get LIF filename (without path)
lifNameArr = split(lifPath, File.separator);
lifName = lifNameArr[lengthOf(lifNameArr)-1];
lifName = replace(lifName, ".lif", "");

// Create log file
logFilename = logDir + File.separator + "export_log.csv";
if (!File.exists(logFilename)) {
    createLogFile(logFilename);
}
else {
    print("Log file exists: " + logFilename);
}

// Get the number of series in the LIF
run("Bio-Formats Macro Extensions");
Ext.setId(lifPath);
Ext.getSeriesCount(seriesCount);

// Log messages
print("Found " + seriesCount + " series in file.");
print("====================================");

// Initialize exported count
exportCount = 0;

// Loop through each series
for (i = 0; i < seriesCount; i++) {
    // Set current series
    Ext.setSeries(i);
    dimensions = SplitSeries(lifPath, i);
    exportCount = SaveSeries(outputDir, lifName, exportCount, i);
}

// Log the export
logExport(logFilename, lifName, seriesCount, exportCount);
print("Exported " + exportCount + " images from " + seriesCount + " series.");

// Close Bio-Formats Macro Extensions
Ext.close();
print("All series processed.");

setBatchMode(false);