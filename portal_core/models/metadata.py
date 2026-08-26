from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, String, ARRAY, ForeignKey, UniqueConstraint, func, Integer
from pydantic import BaseModel, ConfigDict
from portal_core.models.base import Base
from sqlalchemy import Enum
import enum
from datetime import datetime


# Association table for the many-to-many relationship
# book_authors = Table(
#     'book_authors', Base.metadata,
#     Column('book_id', Integer, ForeignKey('books.id')),
#     Column('author_id', Integer, ForeignKey('authors.id'))
# )

# book_editors = Table(
#     'book_editors', Base.metadata,
#     Column('book_id', Integer, ForeignKey('books.id')),
#     Column('editor_id', Integer, ForeignKey('authors.id'))
# )

# class Author(Base):
#     __tablename__ = 'authors'

#     id = Column(Integer, primary_key=True)
#     name = Column(String)

#     books_authored = relationship("Book", secondary=book_authors, back_populates="authors")
#     books_edited = relationship("Book", secondary=book_editors, back_populates="editors")

# class Book(Base):
#     __tablename__ = 'books'

#     id = Column(Integer, primary_key=True)
#     title = Column(String)

#     authors = relationship("Author", secondary=book_authors, back_populates="books_authored")
#     editors = relationship("Author", secondary=book_editors, back_populates="books_edited")


# +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# Example one (Author) to many (Book) relationship
# class Author(db.Model):
#     __tablename__ = 'author'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String)
#     books = relationship("Book", back_populates="author")

# class Book(db.Model):
#     __tablename__ = 'book'
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String)
#     author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
#     author = relationship("Author", back_populates="books")


# TABLES created:
#  public | address                      | table | dash_user
#  public | contact_information          | table | dash_user
#  public | dashboard_user               | table | dash_user
#  public | file                         | table | dash_user
#  public | metadata_role                | table | dash_user
#  public | oads_metadata                | table | dash_user
#  public | oads_metadata_data_submitter | table | dash_user
#  public | oads_metadata_investigators  | table | dash_user
#  public | person                       | table | dash_user
#  public | person_metadata_roles        | table | dash_user
#  public | related_dataset              | table | dash_user
#  public | research_organization        | table | dash_user
#  public | submission                   | table | dash_user
#  public | dashboard_user_people        | table | dash_user

# address, contact_information, dashboard_user, file, metadata_role, oads_metadata, oads_metadata_data_submitter, oads_metadata_investigators, person, person_metadata_roles, related_dataset, research_organization, submission, dashboard_user_people

# This will find processes that have the table locked
# SELECT pid, relname
# FROM pg_locks l
# JOIN pg_class t ON l.relation = t.oid AND t.relkind = 'r'
# WHERE t.relname = 'investigator';

# This will show active and idle in transaction (which is probably what's preventing the action you want)
# select pid,state from pg_stat_activity ;
# You can terminate them with the command below

# SELECT pg_terminate_backend([PID from ABOVE]);
#
# will terminate the process


# class Base(DeclarativeBase):
#     pass


class DashboardUser(Base):
    __tablename__ = "dashboard_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    # could add if desired...  uid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    active: Mapped[Optional[Boolean]] = mapped_column(Boolean, default=True)
    email: Mapped[String] = mapped_column(String, unique=True)
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="dashboard_user"
    )
    people = relationship(
        "Person", secondary="dashboard_user_people", back_populates="dashboard_user"
    )


class DashboardUserPeople(Base):
    __tablename__ = "dashboard_user_people"

    dashboard_user_id = mapped_column(ForeignKey("dashboard_user.id"), primary_key=True)
    person_id = mapped_column(ForeignKey("person.id"), primary_key=True)


class DashboardUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    active: bool
    email: str
    submissions: list["SubmissionSchema"]


# This could be a enum:
# See: https://stackoverflow.com/questions/76268799/how-should-i-declare-enums-in-sqlalchemy-using-mapped-column-to-enable-type-hin
# but I don't expect to let users create roles so if it's just a string we can jigger them as we wish easily
#
# I am going to try using a "join table" to connect person to role so the same person can have many roles
# with no back reference


class Submission(Base):
    __tablename__ = "submission"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, autoincrement=False) # Use create_submission_id in utils.identifier_utils and give user_id to create unique_hash
    submitted_to_ncei: Mapped[Optional[Boolean]] = mapped_column(Boolean)
    date_submitted_to_ncei: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    created: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    modified: Mapped[DateTime] = mapped_column(
        DateTime, onupdate=func.now(), server_default=func.now()
    )
    # Each submission has one metadata document
    oads_metadata: Mapped["OadsMetadata"] = relationship(
        "OadsMetadata",
        uselist=False,
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    files: Mapped[List["File"]] = relationship(
        "File", back_populates="submission", cascade="all, delete-orphan"
    )
    dashboard_user_id: Mapped[int] = mapped_column(ForeignKey("dashboard_user.id"))
    dashboard_user: Mapped["DashboardUser"] = relationship(
        "DashboardUser", back_populates="submissions"
    )


class SubmissionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    submitted_to_ncei: Optional[bool] = False
    date_submitted_to_ncei: Optional[datetime] = None
    created: datetime
    modified: datetime
    # Each submission has one metadata document
    oads_metadata: "OadsMetadataSchema"
    files: list["FileSchema"]


class OadsMetadata(Base):
    __tablename__ = "oads_metadata"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_date: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    title: Mapped[Optional[String]] = mapped_column(
        String, info={"label": "Dataset Submission Title"}
    )
    abstract: Mapped[Optional[String]] = mapped_column(String, info={"label": "Abstract"})
    doi: Mapped[Optional[String]] = mapped_column(String, info={"label": "Digital Object Identifier"})
    use_limitation: Mapped[Optional[String]] = mapped_column(
        String, info={"label": "Use Limitation"}
    )
    purpose: Mapped[Optional[String]] = mapped_column(String, info={"label": "Purpose"})
    data_license: Mapped[Optional[String]] = mapped_column(String, info={"label": "Data License"})
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, info={"label": "Publication Year"})
    dataset_version: Mapped[Optional[str]] = mapped_column(String, info={"label": "Dataset Version"})
    publisher_name: Mapped[Optional[str]] = mapped_column(String, info={"label": "Publisher Name"})
    publisher_location: Mapped[Optional[str]] = mapped_column(String, info={"label": "Publisher Location"})
    doi_requested: Mapped[bool] = mapped_column(Boolean, default=False, info={"label": "DOI Requested"})
    related_datasets: Mapped[Optional[List["RelatedDataset"]]] = relationship(
        back_populates="oads_metadata"
    )
    investigators = relationship(
        "Person",
        secondary="oads_metadata_investigators",
        back_populates="investigator_person",
    )
    data_submitter = relationship(
        "Person",
        secondary="oads_metadata_data_submitter",
        back_populates="data_submitter_person",
    )
    submission_id: Mapped[str] = mapped_column(String(16), ForeignKey("submission.id"))
    submission: Mapped["Submission"] = relationship(back_populates="oads_metadata")


class OadsMetadataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    submission_date: datetime
    title: str
    abstract: str
    doi: Optional[str] = None
    use_limitation: Optional[str] = None
    purpose: Optional[str] = None
    data_license: str
    publication_year: Optional[int] = None
    dataset_version: Optional[str] = None
    publisher_name: Optional[str] = None
    publisher_location: Optional[str] = None
    doi_requested: bool = False
    related_datasets: Optional[list["RelateDatasetdSchema"]]
    investigators: list["PersonSchema"]
    data_submitter: list["PersonSchema"]


class OadsMetadataDataSubmitter(Base):
    __tablename__ = "oads_metadata_data_submitter"
    oads_metadata_id = mapped_column(ForeignKey("oads_metadata.id"), primary_key=True)
    person_id = mapped_column(ForeignKey("person.id"), primary_key=True)


class OadsMetadataInvestigators(Base):
    __tablename__ = "oads_metadata_investigators"

    oads_metadata_id = mapped_column(ForeignKey("oads_metadata.id"), primary_key=True)
    person_id = mapped_column(ForeignKey("person.id"), primary_key=True)

    # temporal_extents: Mapped['TemporalExtents'] = relationship(back_populates='oads_metadata')

    #   <xs:element name="temporalExtents" type="temporal_extents_type"/>
    #   <xs:element name="spatialExtents" type="spatial_extents_type"/>
    #   <xs:element name="spatialReference" type="xs:string" minOccurs="0"/>
    #   <xs:element name="sampleCollectionRegions" minOccurs="0">


class RelatedDataset(Base):
    __tablename__ = "related_dataset"
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset: Mapped[str] = mapped_column(String)
    link: Mapped[str] = mapped_column(String)
    oads_metadata_id = mapped_column(ForeignKey("oads_metadata.id"))
    oads_metadata: Mapped["OadsMetadata"] = relationship(
        back_populates="related_datasets"
    )


class RelateDatasetdSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    dataset: str
    link: str


class ResearchOrganization(Base):
    __tablename__ = "research_organization"
    id: Mapped[String] = mapped_column(String, primary_key=True)
    display_name: Mapped[String] = mapped_column(String)


class ResearchOrganizationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, aribitrary_types_allowed=True)
    id: int
    ror_id: str
    display_name: str

class PersonOrganization(Base):
    __tablename__ = "person_organization"

    person_id = mapped_column(ForeignKey("person.id"), primary_key=True)
    organization_id = mapped_column(ForeignKey("organization.id"), primary_key=True)

class Organization(Base):
    __tablename__ = "organization"
    id: Mapped[int] = mapped_column(primary_key=True)
    ror_id: Mapped[Optional[String]] = mapped_column(String)
    name: Mapped[String] = mapped_column(String)

    # Many-to-Many relationship pointing to Person via the association table string
    people = relationship(
        "Person", 
        secondary="person_organization", 
        back_populates="organizations"
    )

class OrganizationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, aribitrary_types_allowed=True)
    id: int
    ror_id: Optional[str]
    name: str

class Person(Base):
    __tablename__ = "person"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[String]] = mapped_column(
        String, info={"label": "Pre-nominal Title"}
    )
    first_name: Mapped[String] = mapped_column(String, info={"label": "First Name"})
    last_name: Mapped[String] = mapped_column(String, info={"label": "Last Name"})
    orcid_id: Mapped[Optional[str]] = mapped_column(
        String, info={"label": "ORCID ID"}
    )
    orcid_authenticated: Mapped[bool] = mapped_column(
        Boolean, default=False, info={"label": "ORCID Authenticated"}
    )
    organizations = relationship(
        "Organization", 
        secondary="person_organization", 
        back_populates="people"
    )
    contact_information = relationship(
        "ContactInformation", back_populates="person", uselist=False
    )
    metadata_roles = relationship(
        "MetadataRole", secondary="person_metadata_roles", back_populates="person"
    )
    investigator_person = relationship(
        "OadsMetadata",
        secondary="oads_metadata_investigators",
        back_populates="investigators",
    )
    data_submitter_person = relationship(
        "OadsMetadata",
        secondary="oads_metadata_data_submitter",
        back_populates="data_submitter",
    )
    dashboard_user = relationship(
        "DashboardUser",
        secondary="dashboard_user_people",
        back_populates="people",
        uselist=False,
    )

    def __repr__(this):
        if (
            this.contact_information is not None
            and this.contact_information.email is not None
        ):
            an_email = this.contact_information.email
        else:
            an_email = "no email address"
        return f"{this.first_name} {this.last_name} ({an_email})"


class MetadataRole(Base):
    __tablename__ = "metadata_role"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[String] = mapped_column(String)

    person = relationship(
        "Person", secondary="person_metadata_roles", back_populates="metadata_roles"
    )


class MetadataRoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    name: Optional[str] = None


class PersonMetadataRoles(Base):
    __tablename__ = "person_metadata_roles"

    person_id = mapped_column(ForeignKey("person.id"), primary_key=True)
    role_id = mapped_column(ForeignKey("metadata_role.id"), primary_key=True)


class PersonSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    title: Optional[str] = None
    first_name: str
    last_name: str
    orcid_id: str
    orcid_authenticated: bool
    organizations: list["OrganizationSchema"]
    contact_information: Optional["ContactInformationSchema"]


class ContactInformation(Base):
    __tablename__ = "contact_information"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[Optional[String]] = mapped_column(String, info={"label": "Phone"})
    email: Mapped[String] = mapped_column(String, info={"label": "Email"})
    link: Mapped[Optional[String]] = mapped_column(String, info={"label": "Link URL"})
    person_id = mapped_column(
        ForeignKey("person.id"), nullable=True
    )  # Contact information is currently optional via nullable=True
    person = relationship("Person", back_populates="contact_information", uselist=False)
    address = relationship(
        "Address", back_populates="contact_information", uselist=False
    )


class ContactInformationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    phone: Optional[str] = None
    email: str
    link: Optional[str] = None
    address: Optional["AddressSchema"]


class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_points: Mapped[Optional[List[String]]] = mapped_column(
        ARRAY(String),
    )
    city: Mapped[Optional[String]] = mapped_column(String, info={"label": "City"})
    administrative_area: Mapped[Optional[String]] = mapped_column(
        String, info={"label": "State, Provance or AA"}
    )
    postal_code: Mapped[Optional[String]] = mapped_column(
        String, info={"label": "ZIP or Postal Code"}
    )
    country: Mapped[Optional[String]] = mapped_column(String, info={"label": "Country"})
    contact_information_id = mapped_column(
        ForeignKey("contact_information.id"), nullable=True
    )  # Address are optional for contact information
    contact_information = relationship("ContactInformation", back_populates="address")


class AddressSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    delivery_points: Optional[list[str]]
    city: Optional[str]
    administrative_area: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

class FileCategory(str, enum.Enum):
    DATA = "data"
    SUPPLEMENTAL = "supplemental"
    GENERATED = "generated" # used for data files that were edited and resvaed (like in ocean sites)

    @property
    def label(self):
        labels = {
            "data": "Data File",
            "supplemental": "Supplemental File",
            "generated": "Generated File"
        }
        return labels[self.value]

file_category_db_enum = Enum(
    FileCategory,
    native_enum=True,
    name="file_category_enum",
    values_callable=lambda x: [item.value for item in x],
)


class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[String] = mapped_column(String)
    category: Mapped[String] = mapped_column(String)
    mime: Mapped[String] = mapped_column(String)
    created: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    modified: Mapped[DateTime] = mapped_column(
        DateTime, onupdate=func.now(), server_default=func.now()
    )
    submission_id: Mapped[int] = mapped_column(ForeignKey("submission.id"))
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="files"
    )

    # source_file for when category = generated (this points to the original file it is derived from)
    source_file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("file.id"), nullable=True)
    source_file: Mapped[Optional["File"]] = relationship("File", remote_side=[id])

    __table_args__ = (
        UniqueConstraint("source_file_id", name="uq_file_source_file_id"),
    )


class FileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    filename: str
    category: FileCategory
    mime: str
    created: datetime
    modified: datetime
