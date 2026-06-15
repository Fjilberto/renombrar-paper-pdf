Python script to automatically rename poorly formatted scientific PDF files into a clean, standardized format: `Author_Year_Title.pdf`.

How to use:

1) Ensure you have the required library installed: pip install pypdf requests
2) Create a folder with the script and the pdf you want to rename
3) Run the python script, this going to rename each pdf in the folder to the formar "author_year_title": python renombrar_pdf.py
4) Review if the new title is accurate to the paper title. The script will automatically skip files that already match the correct format

Tips in configuration:

1) DRY_RUN = False Set it to True to run a simulation. It will display all the projected name changes in the console without modifying your files. Perfect for testing.
2) DESBLOQUEAR = True When set to True, it automatically runs a background PowerShell command (Unblock-File) to remove Windows security flags from downloaded files, enabling seamless file previews. Set to False to disable.
3) MAX_TITLE_LENGTH = 80 Controls the maximum number of characters allowed for the paper title segment to keep your file names clean and prevent path errors. Adjust the number to your preference.
