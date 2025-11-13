import pandas as pd
from pandas import DataFrame
from datetime import timedelta
import numpy as np

CONFIG_ID_TO_SITE = {
    "default-english-configuration": "default-english-configuration",
    "femina-se-citation-story-config": "femina.se",
    "hant-se-citation-story-config": "hant.se",
    "kk-no-citation-story-config": "kk.no",
    "svensk-dam-se-citation-story-config": "svenskdam.se",
    "se-og-hor-no-citation-story-config": "seoghoer.no",
    "billedbladet-dk-citation-story-config": "billedbladet.dk",
    "dagbladet-sitatsak-dev": "dagbladet.no",
    "dagbladet-sitatsak": "dagbladet.no", 
    "seiska-citation-article": "seiska.fi",
    "sol.no-coeditor-citatsak": "sol.no",
    "se-og-hor-dk-citation-story-config": "seoghoer.dk",
    "femina-dk-citation-story-config": "femina.dk"
}

class CandidateGeneration():
    def __init__(self):
        print("CandidateGeneration initialized")

    def reformat_name(self, name) -> str:
        """        
        Reformat names from "Last, First" to "First Last" and convert to lowercase.
        """
        # Remove "Af" prefix if present
        if pd.isna(name):
            return None

        name = str(name).strip()

        # Remove everything after ' Foto:' (case-insensitive)
        lower_name = name.lower()
        foto_index = lower_name.find(' foto:')
        if foto_index != -1:
            name = name[:foto_index].strip()

        # Remove "Af " prefix if present (case-insensitive)
        if name.lower().startswith("af "):
            name = name[3:].strip()

        # Handle "Last, First" format
        if ',' in name:
            parts = [p.strip() for p in name.split(',')]
            if len(parts) == 2:
                name = f"{parts[1]} {parts[0]}"

        # Keep only first and last names (remove middle names)
        tokens = name.split()
        if len(tokens) >= 2:
            first_name = tokens[0]
            last_name = tokens[-1]
            name = f"{first_name} {last_name}"

        return name.lower()
    
    def data_preparation(self, pages: DataFrame, drafts: DataFrame, users: DataFrame) -> tuple:
        """        
        Prepare data for candidate generation by cleaning and merging dataframes.
        """
        print('Pre-processing data for candidate generation...')
        #Merging drafts and users on user_id to get user names for matching
        drafts_users = pd.merge(
            drafts,
            users[['id', 'first_name', 'last_name']],
            how='left',
            left_on='user_id',
            right_on='id'
        )

        # Reformatting names to match the format between drafts and pages
        # Labrador uses created_by as creator
        pages['created_by_lc'] = pages.apply(
            lambda row: (
                self.reformat_name(row['created_by'])
                if pd.notnull(row['created_by'])
                else str(row['author']).split(',')[0].strip().lower()
                if pd.notnull(row['author'])
                else None
            ),
            axis=1
        )
        drafts_users['full_name'] = drafts_users['first_name'].fillna('') + ' ' + drafts_users['last_name'].fillna('')
        drafts_users['full_name_lc'] = drafts_users['full_name'].str.strip().str.lower()

        # Creating datetime columns for filtering
        drafts_users['created_at_dt'] = pd.to_datetime(drafts_users['created_at'], utc=True)
        pages['published_dt'] = pd.to_datetime(pages['published_ts'], utc=True)

        # Mapping configuration_id to site
        drafts_users['site'] = drafts_users['configuration_id'].map(CONFIG_ID_TO_SITE)

        drafts_users = drafts_users.rename(columns={'embedding': 'embedding_draft'})
        pages = pages.rename(columns={'embedding': 'embedding_published'})

        return pages, drafts_users

    def smooth_decay(self, days_diff, midpoint=7, steepness=0.4) -> np.ndarray:
        """
        Apply a smooth decay function to the time difference.
        """
        return 1 / (1 + np.exp(steepness * (days_diff - midpoint)))


    def create_candidate_pairs(self, pages: DataFrame, drafts: DataFrame) -> DataFrame:
        """
        Create candidate pairs by merging drafts and pages on site, user and time filter.
        """
        print('Generating candidate pairs...')

        # Merge on site config and site domain
        # Merge on full_name_lc ↔ created_by_name_lc
        candidate_pairs = drafts.merge(
            pages,
            left_on=['site', 'full_name_lc'],
            right_on=['site_domain', 'created_by_lc'],
            suffixes=('_draft', '_pub')
        )

        # Filter: published within 14 days after draft
        candidate_pairs = candidate_pairs[
            (candidate_pairs['published_dt'] >= candidate_pairs['created_at_dt']) &
            (candidate_pairs['published_dt'] <= candidate_pairs['created_at_dt'] + timedelta(days=14))
        ]

        candidate_pairs['days_diff'] = (candidate_pairs['published_dt'] - candidate_pairs['created_at_dt']).dt.days

        #slow decay early and steep decay with a halflife of 7 days
        candidate_pairs['time_decay'] = self.smooth_decay(candidate_pairs['days_diff'])

        return candidate_pairs
