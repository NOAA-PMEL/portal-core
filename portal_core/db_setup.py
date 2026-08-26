def init_db(portal=None):
    """
    Import all models and create any missing tables.

    Base models first - portal models subclass Base and declare FKs to
    oads_metadata_id. Same ordering rule as init_extensions().

    Scripts that only touch shared tables can omit `portal`.
    """
    # import portal_core.models.metadata # register base tables
    import portal_core.models.metadata # register base tables
    from portal_core.models import Base
    from portal_core.constants import postgres_engine
    
    if portal is not None:
        portal.load_models()
    Base.metadata.create_all(bind=postgres_engine)