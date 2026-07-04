@echo off
echo Removing generated runtime files from Git tracking while keeping local copies...
git rm --cached -r data/processed
git add data/processed/.gitkeep .gitignore .gitattributes
git commit -m "Stop tracking generated runtime data" || echo Nothing to commit.
echo Done. Now run: git push -u origin main
pause
