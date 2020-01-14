from pathlib import Path

from pydriller.domain.commit import ModificationType
from pydriller.repository_mining import RepositoryMining

class ProcessMetrics():
    """
    This class is responsible to implement the following process metrics:

    - Commit Count - measures the number of commits made to a file
    - Distinct Developers Count - measures the cumulative number of distinct developers that contributed to a file
    - Developers Count Prior Release - counts the number of developer who modified the file durinig the prior release
    """

    def commits_count(self, path_to_repo: str, filepath: str, commit_hash: str = None):
        """
        Return the number of commits made to a file from the first commit to the one identified by commit_hash.
        
        :path_to_repo: path to a single repo
        :commit_hash: the SHA of the commit to stop counting. If None, the analysis starts from the latest commit
        :filepath: the path to the file to count for. E.g. 'doc/README.md'
        
        :return: int number of commits made to the file
        """

        filepath = str(Path(filepath))
        count = 0
        start_counting = commit_hash is None

        for commit in RepositoryMining(path_to_repo, reversed_order=True).traverse_commits():
            
            if not start_counting and commit_hash == commit.hash:
                start_counting = True

            # Skip commit if not counting
            if not start_counting:
                continue
            
            for modified_file in commit.modifications:
                if modified_file.new_path == filepath or modified_file.old_path == filepath:
                    count += 1

                    if modified_file.change_type == ModificationType.RENAME:
                        filepath = str(Path(modified_file.old_path))
                    
                    if modified_file.change_type == ModificationType.ADD:
                        return count

                    break
        return count


    def distinct_dev_count(self, path_to_repo: str, filepath: str, commit_hash: str = None):
        """
        Return the cumulative number of distinct developers contributed to the file up to the indicated commit.
        
        :path_to_repo: path to a single repo
        :commit_hash: the SHA of the commit to stop counting. If None, the SHA is the latest commit SHA
        :filepath: the path to the file to count for. E.g. 'doc/README.md'
        
        :return: int number of distinct developers contributing to the file
        """
        filepath = str(Path(filepath))
        developers = set()
        start_counting = commit_hash is None
        
        for commit in RepositoryMining(path_to_repo, reversed_order=True).traverse_commits():            
            
            if not start_counting and commit_hash == commit.hash:
                start_counting = True

            # Skip commit if not counting
            if not start_counting:
                continue
            
            for modified_file in commit.modifications:

                if modified_file.new_path == filepath or modified_file.old_path == filepath:
                    developers.add(commit.author.email.strip())
                    
                    if modified_file.change_type == ModificationType.RENAME:
                        filepath = str(Path(modified_file.old_path))
                        
                    if modified_file.change_type == ModificationType.ADD:
                        return len(developers)

                    break

        return len(developers)


    def dev_count_prior_release(self, path_to_repo: str, filepath: str, from_commit: str = None, to_commit: str = None):
        """
        Return the number of developers who modified the file during the prior release.
        
        :path_to_repo: path to a single repo
        :from_commit: the SHA of the commit to start counting. If None, the SHA is the first commit SHA
        :to_commit: the SHA of the commit to stop counting. If None, the SHA is the latest commit SHA
        :filepath: the path to the file to count for. E.g. 'doc/README.md'
        
        :return: int number of distinct developers contributing to the file
        """
        developers = set()
        filepath = str(Path(filepath))
        
        # Get the sha of all releases in the repo
        releases = set()
        for commit in RepositoryMining(path_to_repo, from_commit=from_commit, to_commit=to_commit, reversed_order=True, only_releases=True).traverse_commits():
            releases.add(commit.hash)
        
        in_prior_release = False

        for commit in RepositoryMining(path_to_repo, from_commit=from_commit, to_commit=to_commit, reversed_order=True).traverse_commits():
            
            sha = commit.hash
            if sha in releases:
                if not in_prior_release:
                    in_prior_release = True
                    continue # Start count from next iteration
                else:
                    break # Reached another release: stop!

            if not in_prior_release:
                continue

            for modified_file in commit.modifications:

                stop_count = False
                if modified_file.new_path == filepath or modified_file.old_path == filepath:
                    
                    developers.add(commit.author.email.strip())

                    if modified_file.change_type == ModificationType.RENAME:
                        filepath = str(Path(modified_file.old_path))
                
                    elif modified_file.change_type == ModificationType.RENAME:
                        filepath = str(Path(modified_file.old_path))
                        
                    elif modified_file.change_type == ModificationType.ADD:
                        stop_count = True
                    
                    break
                
                if stop_count:
                    break

        return len(developers)
        

    def new_dev_count_prior_release(self, path_to_repo: str, filepath: str, from_commit: str = None, to_commit: str = None):
        """
        Return the number of new developers who modified the file during the prior release.
        
        :path_to_repo: path to a single repo
        :from_commit: the SHA of the commit to start counting. If None, the SHA is the first commit SHA
        :to_commit: the SHA of the commit to stop counting. If None, the SHA is the latest commit SHA
        :filepath: the path to the file to count for. E.g. 'doc/README.md'
        
        :return: int number of distinct developers contributing to the file
        """
        developers = set()
        duplicates = set()
        filepath = str(Path(filepath))
        
        # Get the sha of all releases in the repo
        releases = set()
        for commit in RepositoryMining(path_to_repo, from_commit=from_commit, to_commit=to_commit, reversed_order=True, only_releases=True).traverse_commits():
            releases.add(commit.hash)
        
        in_prior_release = False
        in_older_release = False

        for commit in RepositoryMining(path_to_repo, from_commit=from_commit, to_commit=to_commit, reversed_order=True).traverse_commits():
            
            sha = commit.hash
            if sha in releases:
                if not in_prior_release:
                    in_prior_release = True
                    continue # Start count from next iteration
                else:
                    in_older_release = True # Reached a release older than the prior

            if not in_prior_release:
                continue

            for modified_file in commit.modifications:

                stop_count = False

                if modified_file.new_path == filepath or modified_file.old_path == filepath:
                    
                    author = commit.author.email.strip()

                    if in_older_release and author in developers:
                        duplicates.add(author)
                    else:
                        developers.add(author)
                    
                    if modified_file.change_type == ModificationType.RENAME:
                        filepath = str(Path(modified_file.old_path))
                
                    elif modified_file.change_type == ModificationType.RENAME:
                        filepath = str(Path(modified_file.old_path))
                        
                    elif modified_file.change_type == ModificationType.ADD:
                        stop_count = True
                    
                    break
                
                if stop_count:
                    break
        
        new_devs = developers - duplicates
        return len(new_devs)