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

// Function to split series and save
function SplitSeries(lifPath, i) {
    // Open the series
    run("Bio-Formats Importer", "open=[" + lifPath + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT series_" + i);
    
    // Split the channels (if it contains channels)
    getDimensions(width, height, channels, slices, frames);
    if (channels > 1) {
    	run("Make Substack...", "channels=1");
    }
}

// Function to save the series with a clean name
function SaveSeries(outputDir) {
    // Get series title
    Ext.getSeriesName(seriesName);
    seriesName_arr = split(seriesName, "/");
    cleanSeriesName = seriesName_arr[lengthOf(seriesName_arr)-1];

    // Save the series as TIFF
    savePath = outputDir + File.separator + cleanSeriesName + ".tif";
    saveAs("Tiff", savePath);
    print("Saved to: " + savePath);

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

// Get the number of series in the LIF
run("Bio-Formats Macro Extensions");
Ext.setId(lifPath);
Ext.getSeriesCount(seriesCount);
print("Found " + seriesCount + " series in file.");

// Loop through each series
for (i = 0; i < seriesCount; i++) {
    // Set current series
    Ext.setSeries(i);
    SplitSeries(lifPath, i);
    SaveSeries(outputDir);
}

print("All series processed.");

setBatchMode(false);