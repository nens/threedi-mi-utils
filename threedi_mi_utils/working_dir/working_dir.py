# Copyright (C) 2023 by Lutra Consulting for 3Di Water Management
import json
import os
import re
import shutil
from itertools import chain
from uuid import uuid4

from threedi_schema import ThreediDatabase

DIR_MAX_PATH = 248
FILE_MAX_PATH = 260
UNC_PREFIX = "\\\\?\\"


class LocalSchematisation:
    """Local revision directory structure representation."""

    def __init__(self, working_dir, schematisation_pk, schematisation_name, parent_revision_number=None, create=False):
        self.working_directory = working_dir
        self.id = schematisation_pk
        self.name = schematisation_name
        self.revisions = {}
        self.wip_revision = WIPRevision(self, parent_revision_number) if parent_revision_number is not None else None
        if create:
            self.build_schematisation_structure()

    def add_revision(self, revision_number):
        """Add a new revision."""
        local_revision = LocalRevision(self, revision_number)
        if revision_number in self.revisions and os.path.exists(local_revision.main_dir):
            shutil.rmtree(local_revision.main_dir)
        local_revision.make_revision_structure()
        self.revisions[revision_number] = local_revision
        self.write_schematisation_metadata()
        return local_revision

    def set_wip_revision(self, revision_number):
        """Set a new work in progress revision."""
        if self.wip_revision is not None and os.path.exists(self.wip_revision.main_dir):
            shutil.rmtree(self.wip_revision.main_dir)
        self.wip_revision = WIPRevision(self, revision_number)
        self.wip_revision.make_revision_structure()
        self.write_schematisation_metadata()
        return self.wip_revision

    def update_wip_revision(self, revision_number):
        """Update a work in progress revision number."""
        if self.wip_revision is not None and os.path.exists(self.wip_revision.main_dir):
            self.wip_revision.number = revision_number
            self.write_schematisation_metadata()
            return True
        else:
            return False

    @classmethod
    def initialize_from_location(cls, schematisation_dir, use_config_for_revisions=True):
        """
        Initialize local schematisation structure from the root schematisation dir.
        In case use_config_for_revisions is True, the revisions are derived from the json file,
        otherwise the schematisation dir is scanned for "revision" folders.
        """
        working_dir = os.path.dirname(schematisation_dir)
        if not os.path.isdir(schematisation_dir):
            return None
        config_path = os.path.join(schematisation_dir, "admin", "schematisation.json")
        schema_metadata = cls.read_schematisation_metadata(config_path)
        fallback_id = fallback_name = os.path.basename(schematisation_dir)
        schematisation_pk = schema_metadata.get("id", fallback_id)
        schematisation_name = schema_metadata.get("name", fallback_name)
        local_schematisation = cls(working_dir, schematisation_pk, schematisation_name)

        if use_config_for_revisions:
            revision_numbers = schema_metadata.get("revisions", [])
        else:
            folders = [
                os.path.basename(d) for d in list_dirs(schematisation_dir) if os.path.basename(d).startswith("revision")
            ]
            revision_numbers = [int(re.findall(r"^revision (\d+)", folder)[0]) for folder in folders]

        for revision_number in revision_numbers:
            local_revision = LocalRevision(local_schematisation, revision_number)
            local_schematisation.revisions[revision_number] = local_revision

        wip_parent_revision_number = schema_metadata.get("wip_parent_revision")
        if wip_parent_revision_number is not None:
            local_schematisation.wip_revision = WIPRevision(local_schematisation, wip_parent_revision_number)

        return local_schematisation

    @staticmethod
    def read_schematisation_metadata(schematisation_config_path):
        """Read schematisation metadata from the JSON file."""
        if not os.path.exists(schematisation_config_path):
            return {}
        with open(schematisation_config_path, "r+") as config_file:
            return json.load(config_file)

    def write_schematisation_metadata(self):
        """Write schematisation metadata to the JSON file."""
        schematisation_metadata = {
            "id": self.id,
            "name": self.name,
            "revisions": [local_revision.number for local_revision in self.revisions.values()],
            "wip_parent_revision": self.wip_revision.number if self.wip_revision is not None else None,
        }
        with open(bypass_max_path_limit(self.schematisation_config_path, is_file=True), "w") as config_file:
            config_file_dump = json.dumps(schematisation_metadata)
            config_file.write(config_file_dump)

    def structure_is_valid(self):
        """Check if all schematisation subpaths are present."""
        subpaths_collections = [self.subpaths]
        subpaths_collections += [local_revision.subpaths for local_revision in self.revisions.values()]
        subpaths_collections.append(self.wip_revision.subpaths)
        is_valid = all(os.path.exists(p) if p else False for p in chain.from_iterable(subpaths_collections))
        return is_valid

    @property
    def main_dir(self):
        """Get schematisation main directory."""
        schematisation_dir_path = os.path.normpath(os.path.join(self.working_directory, self.name))
        return schematisation_dir_path

    @property
    def admin_dir(self):
        """Get schematisation admin directory path."""
        admin_dir_path = os.path.join(self.main_dir, "admin")
        return admin_dir_path

    @property
    def subpaths(self):
        """Get schematisation directory sub-paths."""
        paths = [self.admin_dir]
        return paths

    @property
    def schematisation_config_path(self):
        """Get schematisation configuration filepath."""
        config_path = os.path.join(self.admin_dir, "schematisation.json")
        return config_path

    @property
    def schematisation_db_filepath(self):
        """Get schematisation work in progress revision schematisation DB filepath."""
        return self.wip_revision.schematisation_db_filepath

    def build_schematisation_structure(self):
        """Function for schematisation dir structure creation."""
        for schema_sub_path in self.subpaths:
            os.makedirs(bypass_max_path_limit(schema_sub_path), exist_ok=True)
        for local_revision in self.revisions:
            local_revision.make_revision_structure()
        if self.wip_revision is not None:
            self.wip_revision.make_revision_structure()
        self.write_schematisation_metadata()


class LocalRevision:
    """Local revision directory structure representation."""

    def __init__(self, local_schematisation, revision_number):
        self.local_schematisation = local_schematisation
        self.number = revision_number

    def structure_is_valid(self):
        """Check if all revision subpaths are present."""
        is_valid = all(os.path.exists(p) if p else False for p in self.subpaths)
        return is_valid

    @property
    def sub_dir(self):
        """Get schematisation revision subdirectory name."""
        subdirectory = f"revision {self.number}"
        return subdirectory

    @property
    def main_dir(self):
        """Get schematisation revision main directory path."""
        schematisation_dir_path = self.local_schematisation.main_dir
        schematisation_revision_dir_path = os.path.join(schematisation_dir_path, self.sub_dir)
        return schematisation_revision_dir_path

    @property
    def admin_dir(self):
        """Get schematisation revision admin directory path."""
        admin_dir_path = os.path.join(self.main_dir, "admin")
        return admin_dir_path

    @property
    def grid_dir(self):
        """Get schematisation revision grid directory path."""
        if self.number:
            grid_dir_path = os.path.join(self.main_dir, "grid")
            return grid_dir_path

    @property
    def results_dir(self):
        """Get schematisation revision results directory path."""
        grid_dir_path = os.path.join(self.main_dir, "results")
        return grid_dir_path

    @property
    def results_dirs(self):
        """Get all (full) result folders."""
        if not os.path.isdir(self.results_dir):
            return []
        return list_dirs(self.results_dir)

    @property
    def schematisation_dir(self):
        """Get schematisation revision schematisation directory path."""
        grid_dir_path = os.path.join(self.main_dir, "schematisation")
        return grid_dir_path

    @property
    def raster_dir(self):
        """Get schematisation revision raster directory path."""
        rasters_dir_path = os.path.join(self.main_dir, "schematisation", "rasters")
        return rasters_dir_path

    @property
    def schematisation_db_filename(self):
        """ "Get schematisation revision DB filename."""
        db_filename = self.discover_schematisation_db_filename()
        return db_filename

    @property
    def schematisation_db_filepath(self):
        """Get schematisation revision DB filepath."""
        db_filename = self.schematisation_db_filename
        db_filepath = os.path.join(self.schematisation_dir, db_filename) if db_filename else None
        return db_filepath

    @property
    def subpaths(self):
        """Revision directory sub-paths."""
        paths = [
            self.admin_dir,
            self.grid_dir,
            self.results_dir,
            self.schematisation_dir,
            self.raster_dir,
        ]
        return paths

    def discover_schematisation_db_filename(self):
        """Find schematisation revision schematisation DB filepath."""
        db_filename = None
        for db_candidate in os.listdir(self.schematisation_dir):
            db_candidate_filepath = os.path.join(self.schematisation_dir, db_candidate)
            db_candidate_lower = db_candidate.lower()
            if db_candidate_lower.endswith(".gpkg"):
                if is_schematisation_db(db_candidate_filepath):
                    db_filename = db_candidate
                    break
            elif db_candidate_lower.endswith(".sqlite"):
                if is_schematisation_db(db_candidate_filepath):
                    db_filename = db_candidate
        return db_filename

    def make_revision_structure(self, exist_ok=True):
        """Function for schematisation dir structure creation."""
        for subpath in self.subpaths:
            if subpath:
                os.makedirs(bypass_max_path_limit(subpath), exist_ok=exist_ok)

    def backup_schematisation_db(self):
        """Make a backup of the schematisation DB database."""
        backup_db_path = None
        db_filename = self.schematisation_db_filename
        if db_filename:
            backup_folder = os.path.join(self.schematisation_dir, "_backup")
            os.makedirs(bypass_max_path_limit(backup_folder), exist_ok=True)
            prefix = str(uuid4())[:8]
            backup_db_path = os.path.join(backup_folder, f"{prefix}_{db_filename}")
            shutil.copyfile(self.schematisation_db_filepath, bypass_max_path_limit(backup_db_path, is_file=True))
        return backup_db_path


class WIPRevision(LocalRevision):
    """Local Work In Progress directory structure representation."""

    @property
    def grid_dir(self):
        """Get schematisation revision grid directory path."""
        # There is no grid dir in the WIP revision directory.
        return None

    @property
    def results_dir(self):
        """Get schematisation revision results directory path."""
        # There is no result dir in the WIP revision directory.
        return None

    @property
    def subpaths(self):
        """Revision directory sub-paths."""
        paths = [
            self.admin_dir,
            self.schematisation_dir,
            self.raster_dir,
        ]
        return paths

    @property
    def sub_dir(self):
        """Get schematisation revision subdirectory name."""
        subdirectory = "work in progress"
        return subdirectory


def bypass_max_path_limit(path, is_file=False):
    """Check and modify path to bypass Windows MAX_PATH limitation."""
    path_str = str(path)
    if path_str.startswith(UNC_PREFIX):
        valid_path = path_str
    else:
        if is_file:
            if len(path_str) >= FILE_MAX_PATH:
                valid_path = f"{UNC_PREFIX}{path_str}"
            else:
                valid_path = path_str
        else:
            if len(path_str) > DIR_MAX_PATH:
                valid_path = f"{UNC_PREFIX}{path_str}"
            else:
                valid_path = path_str
    return valid_path


def list_dirs(pth):
    """Returns a (non-recursive) list of directories in a specific path."""
    return [os.path.join(pth, dir_name) for dir_name in os.listdir(pth) if os.path.isdir(os.path.join(pth, dir_name))]


def list_local_schematisations(working_dir, use_config_for_revisions=True):
    """Get local schematisations present in the given directory."""
    local_schematisations = {}
    for basename in os.listdir(working_dir):
        full_path = os.path.join(working_dir, basename)
        local_schematisation = LocalSchematisation.initialize_from_location(full_path, use_config_for_revisions)
        if local_schematisation is not None:
            local_schematisations[local_schematisation.id] = local_schematisation
    return local_schematisations


def replace_revision_data(source_revision, target_revision):
    """Replace target revision content with the source revision data."""
    shutil.rmtree(target_revision.main_dir)
    shutil.copytree(source_revision.main_dir, target_revision.main_dir)


def is_schematisation_db(db_filepath):
    """Check if database file is actually a schematisation DB file."""
    db_ext = db_filepath.lower().rsplit(".", maxsplit=1)[-1]
    if db_ext not in ["gpkg", "sqlite"]:
        return False

    db = ThreediDatabase(db_filepath)
    version_num = int(db.schema.get_version())
    if not version_num:
        return False

    if db_ext == "gpkg" and version_num < 300:
        return False
    return True
