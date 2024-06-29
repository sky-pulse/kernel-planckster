import random
import uuid
from typing import List
from faker import Faker
from lib.core.usecase.extend_research_context_usecase import ExtendResearchContextUseCase
from lib.core.usecase_models.extend_research_context_usecase_models import (
    ExtendResearchContextRequest,
    ExtendResearchContextResponse,
)
from lib.infrastructure.config.containers import ApplicationContainer
from lib.infrastructure.controller.extend_research_context_controller import (
    ExtendResearchContextController,
    ExtendResearchContextControllerParameters,
)
from lib.core.view_model.new_research_context_view_mode import NewResearchContextViewModel
from lib.infrastructure.repository.sqla.database import TDatabaseFactory
from lib.infrastructure.repository.sqla.models import (
    SQLALLM,
    SQLAResearchContext,
    SQLASourceData,
    SQLAClient,
)


def test_extend_research_context_presenter(app_container: ApplicationContainer) -> None:
    presenter = app_container.extend_research_context_feature.presenter()
    assert presenter is not None


def test_extend_research_context_usecase(
    app_initialization_container: ApplicationContainer,
    db_session: TDatabaseFactory,
    fake: Faker,
    fake_client_with_conversation: SQLAClient,  # Fake client with Research Context
    fake_source_data_list: list[SQLAResearchContext],
) -> None:
    usecase: ExtendResearchContextUseCase = app_initialization_container.extend_research_context_feature.usecase()

    assert usecase is not None

    client_with_context = fake_client_with_conversation
    llm_name = fake.name()

    # Make sure all source data have valid, unique IDs
    existing_source_data_ids = []
    for context in client_with_context.research_contexts:
        existing_source_data_ids.extend([sd.id for sd in context.source_data])

    incoming_source_data_list = fake_source_data_list
    new_source_data_list: List[SQLASourceData] = []
    for source_data in incoming_source_data_list:
        while source_data.id is None or source_data.id in existing_source_data_ids + new_source_data_list:
            source_data.id = random.randint(1001, 2000)
        new_source_data_list.append(source_data)
    client_with_context.source_data.extend(new_source_data_list)
    new_source_data_ids = [sd.id for sd in new_source_data_list]

    llm = SQLALLM(
        llm_name=llm_name,
        research_contexts=client_with_context.research_contexts,
    )

    existing_research_context = random.choice(client_with_context.research_contexts)
    # Make titles unique to query later
    existing_research_context_title = f"{existing_research_context.title}-{uuid.uuid4()}"
    existing_research_context.title = existing_research_context_title

    with db_session() as session:
        client_with_context.save(session=session, flush=True)
        session.commit()

    with db_session() as session:
        queried_existing_research_context = (
            session.query(SQLAResearchContext).filter_by(title=existing_research_context_title).first()
        )

        assert queried_existing_research_context is not None

        queried_client = session.get(SQLAClient, queried_existing_research_context.client_id)

        assert queried_client is not None

        # Details for new Research Context data
        new_research_context_title = f"{fake.name().replace(' ', '_')}-{uuid.uuid4()}"
        new_research_context_description = f"{fake.text()}-{uuid.uuid4()}"

        request = ExtendResearchContextRequest(
            new_research_context_title=new_research_context_title,
            new_research_context_description=new_research_context_description,
            client_sub=queried_client.sub,
            llm_name=llm_name,
            new_source_data_ids=new_source_data_ids,
            existing_research_context_id=queried_existing_research_context.id,
        )
        response = usecase.execute(request=request)

        assert response is not None
        assert isinstance(response, ExtendResearchContextResponse)

        assert response.research_context is not None

        queried_new_research_context = session.get(SQLAResearchContext, response.research_context.id)

        assert queried_new_research_context is not None

        queried_new_research_context_source_data_list = queried_new_research_context.source_data
        queried_new_research_context_source_data_ids = [sd.id for sd in queried_new_research_context_source_data_list]

        existing_source_data_overlap_check = [
            sd.id
            for sd in queried_existing_research_context.source_data
            if sd.id not in queried_new_research_context_source_data_ids
        ]

        assert len(existing_source_data_overlap_check) == 0

        new_source_data_overlap_check = [
            sd_id for sd_id in new_source_data_ids if sd_id not in queried_new_research_context_source_data_ids
        ]

        assert len(new_source_data_overlap_check) == 0

        # Check uniqueness
        assert len(queried_new_research_context_source_data_ids) == len(
            set(queried_new_research_context_source_data_ids)
        )


def test_extend_research_context_controller(
    app_initialization_container: ApplicationContainer,
    db_session: TDatabaseFactory,
    fake: Faker,
    fake_client_with_conversation: SQLAClient,
    fake_source_data_list: list[SQLAResearchContext],
) -> None:
    controller: ExtendResearchContextController = (
        app_initialization_container.extend_research_context_feature.controller()
    )

    assert controller is not None

    client_with_context = fake_client_with_conversation
    llm_name = fake.name()

    # Make sure all source data have valid, unique IDs
    existing_source_data_ids = []
    for context in client_with_context.research_contexts:
        existing_source_data_ids.extend([sd.id for sd in context.source_data])

    incoming_source_data_list = fake_source_data_list
    new_source_data_list: List[SQLASourceData] = []
    for source_data in incoming_source_data_list:
        while source_data.id is None or source_data.id in existing_source_data_ids + new_source_data_list:
            source_data.id = random.randint(2001, 3000)
        new_source_data_list.append(source_data)
    client_with_context.source_data.extend(new_source_data_list)
    new_source_data_ids = [sd.id for sd in new_source_data_list]

    llm = SQLALLM(
        llm_name=llm_name,
        research_contexts=client_with_context.research_contexts,
    )

    existing_research_context = random.choice(client_with_context.research_contexts)
    # Make titles unique to query later
    existing_research_context_title = f"{existing_research_context.title}-{uuid.uuid4()}"
    existing_research_context.title = existing_research_context_title

    with db_session() as session:
        client_with_context.save(session=session, flush=True)
        session.commit()

    with db_session() as session:
        queried_existing_research_context = (
            session.query(SQLAResearchContext).filter_by(title=existing_research_context_title).first()
        )

        assert queried_existing_research_context is not None

        queried_client = session.get(SQLAClient, queried_existing_research_context.client_id)

        assert queried_client is not None

        # Details for new Research Context data
        new_research_context_title = f"{fake.name().replace(' ', '_')}-{uuid.uuid4()}"
        new_research_context_description = f"{fake.text()}-{uuid.uuid4()}"

        controller_parameters = ExtendResearchContextControllerParameters(
            new_research_context_title=new_research_context_title,
            new_research_context_description=new_research_context_description,
            client_sub=queried_client.sub,
            llm_name=llm_name,
            new_source_data_ids=new_source_data_ids,
            existing_research_context_id=queried_existing_research_context.id,
        )
        view_model = controller.execute(parameters=controller_parameters)

        assert view_model is not None
        assert isinstance(view_model, NewResearchContextViewModel)

        assert view_model.research_context_id is not None

        queried_new_research_context = session.get(SQLAResearchContext, view_model.research_context_id)

        assert queried_new_research_context is not None

        queried_new_research_context_source_data_list = queried_new_research_context.source_data
        queried_new_research_context_source_data_ids = [sd.id for sd in queried_new_research_context_source_data_list]

        existing_source_data_overlap_check = [
            sd.id
            for sd in queried_existing_research_context.source_data
            if sd.id not in queried_new_research_context_source_data_ids
        ]

        assert len(existing_source_data_overlap_check) == 0

        new_source_data_overlap_check = [
            sd_id for sd_id in new_source_data_ids if sd_id not in queried_new_research_context_source_data_ids
        ]

        assert len(new_source_data_overlap_check) == 0

        # Check uniqueness
        assert len(queried_new_research_context_source_data_ids) == len(
            set(queried_new_research_context_source_data_ids)
        )