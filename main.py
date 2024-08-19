import os
import sys
import shutil
import hashlib
from datetime import datetime
import time


class SyncFiles:
    """Perform a one-way synchronization of the source folder into a replica folder periodically,
    maintaining a full, identical copy of the source folder.

    Attributes:
        list_dirs: Returns a list with every folder present in the target path.
        sync_folders: Create and delete replica folders according to Source.
        list_files: Return every file in the target path.
        compare_files: Compares a file present in source and replica to check for changes.
        sync_files: Delete, add and modify (replace) files in replica to match source.
        full_sync: Call sync functions and reset list variables holding files and folders.
        add_log: Add a log entry to the file and print it into the terminal.
    """
    def __init__(self, source_path, replica_path, log_path, sync_interval, source_folders=[], replica_folders=[], source_files=[], replica_files=[]):
        """ Inits SyncFiles

        Args:
            source_path: Path to the directory that is going to be synced.
            replica_path: Destination directory for the synced content.
            log_path: Path to the log file.
            sync_interval: Interval (in seconds) of time to re-run the program.
            source_folders: List holding every folder in the source directory and sub-directories.
            replica_folders: List holding every folder in the replica directory and sub-directories.
            source_files: List holding every file in the source directory and sub-directories.
            replica_files: List holding every file in the replica directory and sub-directories.
        """
        self.source_path = source_path
        self.replica_path = replica_path
        self.log_path = log_path
        self.sync_interval = sync_interval
        self.source_folders = list(source_folders)
        self.replica_folders = list(replica_folders)
        self.source_files = list(source_files)
        self.replica_files = list(replica_files)


    def list_dirs(self, target_folder_content: list, path="."):
        """ Returns a list with every folder inside target_folder. This is used to list everything under the source and replica folders.

        Args:
            target_folder_content: List holding every folder inside the target folder.
            path: Path to the to-be scanned folder.
        """
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    target_folder_content.append("\\".join(entry.path.split("\\")[2::]))
                    self.list_dirs(target_folder_content, entry.path)

        return target_folder_content


    def sync_folders(self):
        """ Create and delete folders inside the Replica folder according to what is present in Source folder."""
        source_dirs = self.list_dirs(self.source_folders, self.source_path)
        replica_dirs = self.list_dirs(self.replica_folders, self.replica_path)

        # create dirs
        for i in range(len(source_dirs)):
            if (os.path.exists(os.path.join(self.replica_path, source_dirs[i])) == False and os.path.exists(os.path.join(self.source_path, source_dirs[i]))):
                os.mkdir(os.path.join(self.replica_path, source_dirs[i]))
                self.add_log("CREATED", os.path.join(self.replica_path, source_dirs[i]), self.log_path)

        # delete dirs and contents
        for i in range(len(replica_dirs)):
            if (os.path.exists(os.path.join(self.replica_path, replica_dirs[i])) and os.path.exists(os.path.join(self.source_path, replica_dirs[i])) == False):
                shutil.rmtree(os.path.join(self.replica_path, replica_dirs[i]))
                self.add_log("REMOVED", os.path.join(self.replica_path, replica_dirs[i]), self.log_path)


    def list_files(self, file_list: list, path="."):
        """ Returns a list with every file present inside the target directory.

        Args:
            file_list: List holding every file.
            path: Path to the to-be scanned folder
        """
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    file_list.append("\\".join(entry.path.split("\\")[2::]))
                elif entry.is_dir():
                    self.list_files(file_list, entry.path)
        
        return file_list


    def compare_files(self, source_file, replica_file):
        """ Return the comparison between two hashed files.

        Args:
            source_file: File present in the source folder.
            replica_file: File present in the replica folder.
        """
        BUFF_SIZE = 65536

        src = hashlib.sha256()
        rep = hashlib.sha256()
        
        with open(source_file, 'rb') as f:
            while True:
                data = f.read(BUFF_SIZE)                
                if not data:
                    break
                src.update(data)
        
        with open(replica_file, 'rb') as f:
            while True:
                data = f.read(BUFF_SIZE)
                if not data:
                    break
                rep.update(data)

        return src.hexdigest() == rep.hexdigest()


    def sync_files(self):
        """ Delete, add and modify files """
        source_files = self.list_files(self.source_files, self.source_path)
        replica_files = self.list_files(self.replica_files, self.replica_path)

        # copy
        for i in range(len(source_files)):
            rep_file = os.path.join(self.replica_path, source_files[i])
            src_file = os.path.join(self.source_path, source_files[i])

            if (os.path.exists(rep_file) == False and os.path.exists(src_file)):
                shutil.copy2(src_file, rep_file)
                self.add_log("CREATED", rep_file, self.log_path)
            elif (os.path.exists(rep_file) and os.path.exists(src_file)):
                # checks if the files are exactly the same
                if (self.compare_files(rep_file, src_file) == False):
                    # remove the "original" file 
                    os.remove(rep_file)
                    # replace with updated version
                    shutil.copy2(src_file, rep_file)
                    self.add_log("MODIFIED", rep_file, self.log_path)

        # delete
        for i in range(len(replica_files)):
            if(os.path.exists(os.path.join(self.replica_path, replica_files[i])) and os.path.exists(os.path.join(self.source_path, replica_files[i])) == False):
                os.remove(os.path.join(self.replica_path, replica_files[i]))
                self.add_log("REMOVED", os.path.join(self.replica_path, replica_files[i]), self.log_path)


    def full_sync(self):
        """ Call sync folders and files functions and resets the list values for future use. """
        self.sync_folders()
        self.sync_files()
        
        # reset folder/file lists
        self.source_folders = []
        self.source_files = []
        self.replica_folders = []
        self.replica_files = []


    def add_log(self, action, changes_path, file_path):
        """ Adds a log entry to the file detailing what happened
        
        Args:
            action: Log weather the file/directory was CREATED, COPIED, REMOVED or MODIFIED.
            changes_path: Path of the file/directory that has been changed.
            file_path: Path of the log file.
        """
        now = datetime.now()
        currTimestamp = now.strftime("%d/%b/%Y %H:%M:%S")

        log_message = f"{currTimestamp} [ {action} ] {changes_path}"
        print(log_message)
        with open(file_path, "a") as f:
            f.write(f"{log_message}\n")


if __name__ == '__main__':
    if(len(sys.argv) == 5):
        # check if the directories from the user input exist
        for i in sys.argv[1:4]:
            dir = os.path.abspath(i)
            if os.path.exists(dir) == False:
                raise FileNotFoundError(f"'{dir}' doesn't exist")
        # check if sync_interval is a number
        if (sys.argv[4].isnumeric() == False):
            raise ValueError("sync_interval must be a number.")
        # call function periodically
        while True:
            SyncFiles(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]).full_sync()
            time.sleep(int(sys.argv[4]))
    else:
        raise TypeError(f"Expected 4 arguments, got {len(sys.argv) - 1}")
